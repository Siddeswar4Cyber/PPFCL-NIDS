"""Verify persisted P1 fit populations, transforms and model-ready artifacts."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import duckdb
from audit_datasets import lit,write_json
from preprocess_p1 import sha, fitting_predicate, vector_sql, ALLOWED

ROOT=Path(__file__).resolve().parents[1]


def main():
    results=[]; verification=[]
    for name in ['cic-ids-2017','ND-UNSW-NB15-v3']:
        r=json.loads((ROOT/'reports/preprocessing'/f'{name}.json').read_text())
        assert r['status']=='COMPLETED'
        assert r['script_sha256']==sha(ROOT/'scripts/preprocess_p1.py')
        assert r['cleaned']['sha256']==sha(r['cleaned']['path'])
        con=duckdb.connect()
        try:
            con.execute("SET memory_limit='4GB'"); con.execute('SET threads=8')
            con.execute(f"CREATE VIEW cleaned AS SELECT * FROM read_parquet({lit(r['cleaned']['path'])})")
            assert con.execute('SELECT count(*),count(DISTINCT (source_file,parsed_row)) FROM cleaned').fetchone()==(r['cleaned']['rows'],r['cleaned']['rows'])
            for pipe in r['pipelines']:
                protocol=pipe['protocol']; params=json.loads(Path(pipe['transform_path']).read_text())
                assert sha(pipe['transform_path'])==pipe['transform_sha256']
                assert sha(pipe['fit_membership'])==pipe['fit_membership_sha256']==params['fit_membership_sha256']
                con.execute(f"CREATE OR REPLACE VIEW ids AS SELECT * FROM read_parquet({lit(pipe['fit_membership'])})")
                con.execute('CREATE OR REPLACE VIEW selected AS SELECT c.* FROM cleaned c JOIN ids i USING(source_file,parsed_row,group_id)')
                assert con.execute('SELECT count(*) FROM selected').fetchone()[0]==params['fit_rows']==100000
                assert con.execute(f'SELECT count(*) FROM selected WHERE NOT ({fitting_predicate(protocol)})').fetchone()[0]==0
                difference=con.execute(f"SELECT count(*) FROM ((SELECT group_id FROM cleaned WHERE {fitting_predicate(protocol)} ORDER BY sha256('pilot17|' || group_id),group_id LIMIT 100000) EXCEPT (SELECT group_id FROM ids))").fetchone()[0]
                assert difference==0
                digest=hashlib.sha256()
                for (g,) in con.execute('SELECT group_id FROM ids ORDER BY group_id').fetchall(): digest.update((g+'\n').encode('ascii'))
                assert digest.hexdigest()==params['fit_group_set_sha256']
                expr=[]
                for i in range(1,len(params['parameters'])+1): expr.extend([f'median(clean_x[{i}])',f'max(abs(clean_x[{i}]))',f'count(clean_x[{i}])'])
                values=con.execute('SELECT '+','.join(expr)+' FROM selected').fetchone()
                for i,p in enumerate(params['parameters']):
                    median,maximum,observed=values[3*i:3*i+3]
                    assert p['median']==(median if median is not None else 0)
                    assert p['fit_max_abs']==(maximum or 0) and p['observed_fit_rows']==observed
                    assert p['scale']>=max(1,maximum or 0) and math.frexp(p['scale'])[0]==0.5
                    assert p['scale']==1 or p['scale']/2<(maximum or 0)
                for partition,artifact in pipe['artifacts'].items():
                    assert sha(artifact['path'])==artifact['sha256']
                    con.execute(f"CREATE OR REPLACE VIEW output AS SELECT * FROM read_parquet({lit(artifact['path'])})")
                    if partition=='train':
                        source='selected'; expected=params['fit_rows']
                    else:
                        con.execute(f"CREATE OR REPLACE VIEW permitted_validation AS SELECT * FROM cleaned WHERE quality_eligible AND {ALLOWED[protocol]}='validation'")
                        source='permitted_validation'; expected=con.execute('SELECT count(*) FROM permitted_validation').fetchone()[0]
                    counts=con.execute('SELECT count(*),count(DISTINCT (source_file,parsed_row)) FROM output').fetchone()
                    assert counts==(expected,expected)
                    matched=con.execute(f'''SELECT count(*),count(*) FILTER (WHERE o.vector IS DISTINCT FROM {vector_sql(params)} OR o.label<>c.label OR o.binary_label<>c.binary_label)
                        FROM output o JOIN {source} c USING(source_file,parsed_row,group_id)''').fetchone()
                    assert matched==(expected,0)
                for task in ([1,2] if protocol=='cl' else [None]):
                    for role in ['public_reference','development_train','private_train','validation','sealed_test']:
                        records=[x for x in pipe['support'] if x['role']==role and (task is None or x['task_id']==task)]
                        assert {x['binary_label'] for x in records if x['groups']>0}=={0,1}
                assert all(pipe['validation'][k]==0 for k in ['finite_shape_failures','observed_roundtrip_failures','merged_S1_groups'])
                verification.append({'dataset':name,'protocol':protocol,'fit_scope_and_sampling':'PASSED','fit_parameters_recomputed':'PASSED','artifact_hashes':'PASSED','model_ready_rows_and_vectors':'PASSED','binary_role_task_support':'PASSED','transformed_overlap':pipe['validation']})
                print(f'{name}/{protocol}: persisted verification PASSED',flush=True)
        finally: con.close()
        results.append(r)
    write_json(ROOT/'reports/preprocessing/verification.json',{'status':'PASSED','version':'P1','checks':verification,'tests':'Four P1 fixtures plus seven existing audit/split fixtures','limitation':'Binary64 development artifacts; no DP preprocessing authorization, float32 guarantee, or external performance evaluation'})
    lines=['# CP4 preprocessing results','', 'P1 / M0.4, 2026-09-09. Fitted preprocessing only; no classifier or detection score.','',
        'Five pipelines passed persisted-artifact verification. Their fit populations are exactly the permitted 100,000-representative samples. Recomputed medians, observed counts and maxima match saved parameters; model-ready vectors reproduce exactly from saved transformations. No pipeline merges distinct admitted S1 groups.','',
        '| Dataset | Ledger rows | Quality-invalid rows | Also S1-conflicted | Eligible rows | Peak sampled RSS (GiB) | Runtime (s) |','|---|---:|---:|---:|---:|---:|---:|']
    for r in results:
        bad=sum(x['rows'] for x in r['quality_support'] if x['quality_invalid'])
        both=sum(x['rows'] for x in r['quality_support'] if x['quality_invalid'] and x['primary_role']=='quarantine_conflict')
        eligible=sum(x['rows'] for x in r['quality_support'] if x['quality_eligible'])
        lines.append(f"| {r['dataset']} | {r['cleaned']['rows']:,} | {bad:,} | {both:,} | {eligible:,} | {r['sampled_peak_process_rss_bytes']/2**30:.3f} | {r['elapsed_seconds']:.3f} |")
    for r in results:
        lines += ['',f"## {r['dataset']}",'',f"[Full counts and hashes](preprocessing/{r['dataset']}.json). Quality-invalid rows remain in the ledger; S1 memberships are unchanged.",'',
            '| Class | Additional quality exclusions beyond S1 | Eligible rows |','|---|---:|---:|']
        by_label=defaultdict(lambda:[0,0])
        for x in r['quality_support']:
            if x['quality_invalid'] and x['primary_role']!='quarantine_conflict': by_label[x['label']][0]+=x['rows']
            if x['quality_eligible']: by_label[x['label']][1]+=x['rows']
        for label,(excluded,eligible) in sorted(by_label.items()): lines.append(f'| {label} | {excluded:,} | {eligible:,} |')
        lines += ['', '| Pipeline | Fit rows | Output fields | Validation rows | Verified distinct groups |','|---|---:|---:|---:|---:|']
        for p in r['pipelines']:
            n=sum(x['rows'] for x in p['artifacts']['validation']['binary_support'])
            lines.append(f"| {p['protocol']} | {p['fit_rows']:,} | {p['output_features']} | {n:,} | {p['validation']['verified_groups']:,} |")
        lines += ['', '| Pilot class | Primary | Stress | CL task 1 |','|---|---:|---:|---:|']
        support={}
        for p in r['pipelines']:
            params=json.loads(Path(p['transform_path']).read_text()); support[p['protocol']]={x['label']:x['rows'] for x in params['fit_label_support']}
        for label in sorted(by_label): lines.append(f"| {label} | {support.get('primary',{}).get(label,0):,} | {support.get('stress',{}).get(label,0):,} | {support.get('cl',{}).get(label,0) if 'cl' in support else 'N/A'} |")
        lines += ['', 'Pilot sampling is label-independent. Missing or tiny minority classes restrict any multiclass experiment; no new seed or resampling was used to hide that limitation. Full eligible validation retains its observed prevalence.']
    lines += ['', '## Acceptance and remaining limits','',
        'Accept P1 for the non-private binary CPU baseline pilot in double precision. Preserve each pipeline namespace and exact fitting sample. The CL transform is fitted on task 1 only. Public/private reference/training rows never influence these development parameters; a future DP experiment needs a separately reviewed public or private preprocessing path.','',
        'No clipping, feature selection or constant removal was applied. Missing and unavailable-window indicators preserve distinctions during imputation. Numeric treatment of port/protocol codes is an explicit baseline limitation; alternative encodings require controlled comparison and renewed overlap checks. Float32 conversion is not validated by these binary64 checks.','',
        'All external ordered candidate names and dictionary bytes match after stripping dictionary-key whitespace, but the dictionaries contain ambiguous direction and IAT descriptions and omit IAT units. See [external schema check](preprocessing/external-schema-check.json). Zero-shot extraction equivalence and cross-domain transformed overlap remain unresolved; no external score was inspected.','',
        'Next: CP5 / EXP-003 installs and validates the CPU baseline stack, runs the bounded resource pilot on these exact training samples, and evaluates selection-only validation. Final-test prediction remains sealed.']
    (ROOT/'reports/CP4-preprocessing-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    path=ROOT/'docs/registries/project.json'; project=json.loads(path.read_text()); run=next(x for x in project['runs'] if x['run_id']=='RUN-002-P1')
    run.update(status='COMPLETED',preprocessing_version='P1',split_version='S1',architecture_version='A0',seed=17,
        model='N/A - preprocessing',dataset_version='EXP-001 source hashes, S1 memberships',feature_set='77 CIC / 49 NF inputs; 156 / 98 encoded numeric and indicator fields',
        hyperparameters={'fit_sample_cap':100000,'imputation':'permitted-sample exact median','scaling':'power-of-two maximum absolute','dtype':'float64','feature_selection':False},
        environment_versions={'python':'3.13.13','duckdb':'1.5.5','psutil':'7.2.2'},hardware='reports/audit/environment.json',
        privacy_configuration='No privacy claim; development-fitted preprocessors excluded from privacy-confirmatory authorization',
        cl_configuration='NF transform fitted on task 1 only; frozen for task 2',
        metrics={'pipelines':len(verification),'fit_rows_each':100000,'merged_S1_groups':0,'verified_ledger_rows':sum(r['cleaned']['rows'] for r in results)},
        runtime={r['dataset']:r['elapsed_seconds'] for r in results},memory_usage={r['dataset']:r['sampled_peak_process_rss_bytes'] for r in results},
        artifacts=['reports/CP4-preprocessing-results.md','reports/preprocessing/verification.json','reports/preprocessing/transforms','reports/preprocessing/external-schema-check.json'],
        logs=['reports/preprocess-console-P1.log','reports/preprocess-tests-P1.log'],result='Five verified finite baseline preprocessors and model-ready training/validation artifacts',
        decision='Advance to bounded non-private CPU baseline pilot; retain precision/privacy/external gates')
    if not any(d['decision_id']=='DEC-015' for d in project['decisions']):
        project['decisions'].append({'decision_id':'DEC-015','question':'Which initial preprocessing preserves S1 and permitted fitting boundaries?',
            'candidate_alternatives':['Silent zero replacement and global scaling','P1 medians, explicit indicators and non-clipping binary64 scaling'],
            'evidence_considered':['docs/CP4-preprocessing-P1.md','reports/CP4-preprocessing-results.md'],'experiments_used':['EXP-002'],
            'selected_option':'P1 for the initial non-private CPU pilot','why_selected':'All five fitting scopes and transformed equality checks pass',
            'rejected_alternatives':['Clipping negative values to zero','Fitting CL preprocessing on both tasks','Using development-fitted parameters as a DP preprocessing release'],
            'why_rejected':'Would erase distinctions, leak future statistics, or exceed the reviewed privacy boundary',
            'risks':['Nominal codes treated numerically','Minority sample support','Unverified historical extractor semantics'],
            'trade_offs':['Indicator features increase width','Conservative quality exclusions reduce population','No float32 guarantee'],
            'confidence':'High for persisted numeric/role checks; predictive utility untested','architecture_version':'A0','revisit_condition':'Baseline resource/utility evidence, encoding comparison, precision or privacy mechanism change'})
    project['progress'].update(checkpoint='CP4',status='COMPLETE',current=[],next=['CP5 / EXP-003: pinned CPU baseline stack, bounded 100000-record pilot and selection-only validation'])
    project['progress']['completed']=list(dict.fromkeys(project['progress']['completed']+['P1 deterministic cleaning and five permitted-sample preprocessors','Persisted vector and transformed-overlap verification']))
    project['progress']['needs_validation']=['Baseline detection utility and runtime','Float32/GPU precision and transformed overlap','External extractor semantics and cross-domain overlap','Privacy-specific preprocessing and release accounting','All FL and CL model results']
    project['failures'].append({'experiment_id':'EXP-002','what_failed':'External dictionary exact-key lookup','error':'Eight IAT dictionary keys contain trailing whitespace','suspected_cause':'Dictionary formatting','investigation':'Trimmed unique keys match headers; ambiguous descriptions remain unresolved','fix':'Explicit whitespace normalization with uniqueness check; preserve original bytes','scientifically_invalid':False,'rerun_required':False})
    project['failures']=list({json.dumps(f,sort_keys=True):f for f in project['failures']}.values())
    write_json(path,project)
    print('CP4 verification PASSED')


if __name__=='__main__': main()
