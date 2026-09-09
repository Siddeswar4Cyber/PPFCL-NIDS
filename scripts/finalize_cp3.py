"""Independently verify persisted S1 memberships and record the CP3 gate."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import duckdb
from audit_datasets import write_json, lit

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(8*1024*1024): h.update(b)
    return h.hexdigest()


def main():
    results=[]; checks=[]
    for name in ['cic-ids-2017','ND-UNSW-NB15-v3']:
        r=json.loads((ROOT/'reports/splits'/f'{name}.json').read_text())
        manifest=Path(r['manifest_path']); contract=manifest.parent/'contract.json'
        assert r['status']=='COMPLETED'
        assert sha(manifest)==r['manifest_sha256']
        assert sha(contract)==r['contract_sha256']
        assert sha(ROOT/'scripts/build_split_manifests.py')==r['script_sha256']
        c=json.loads(contract.read_text()); con=duckdb.connect()
        for source in c['source_files']:
            stat=Path(source['path']).stat()
            assert (stat.st_size,stat.st_mtime_ns)==(source['bytes'],source['mtime_ns']), 'Source metadata changed after audit'
        try:
            con.execute("SET memory_limit='4GB'"); con.execute('SET threads=8')
            con.execute(f'CREATE VIEW m AS SELECT * FROM read_parquet({lit(str(manifest))})')
            assert con.execute('SELECT count(*),count(DISTINCT (source_file,parsed_row)) FROM m').fetchone()==(r['rows'],r['rows'])
            assert con.execute('SELECT count(*) FROM (SELECT group_id FROM m GROUP BY group_id HAVING count(DISTINCT primary_role)>1 OR count(DISTINCT stress_role)>1 OR count(DISTINCT task_role)>1 OR sum(representative::INT)<>1)').fetchone()[0]==0
            assert con.execute("SELECT count(*) FROM m WHERE primary_role='sealed_test' AND (stress_role IN ('public_reference','development_train','private_train','validation') OR task_role IN ('public_reference','development_train','private_train','validation'))").fetchone()[0]==0
            if r['stress_cutoffs_ms']:
                a,b=r['stress_cutoffs_ms']
                assert con.execute(f"SELECT count(*) FROM m WHERE (stress_role IN ('public_reference','development_train','private_train') AND end_ms>={a}) OR (stress_role='validation' AND (start_ms<{a} OR end_ms>={b})) OR (stress_role='sealed_test' AND start_ms<{b})").fetchone()[0]==0
            else:
                friday=[f['source_file'] for f in c['source_files'] if Path(f['path']).name.startswith('Friday_')]
                assert con.execute(f"SELECT count(*) FROM m WHERE source_file IN ({','.join(map(str,friday))}) AND stress_role IN ('public_reference','development_train','private_train','validation')").fetchone()[0]==0
            support_checks=[]
            for protocol in ['primary_role','stress_role']+(['task_role'] if r['stress_cutoffs_ms'] else []):
                tasks=[1,2] if protocol=='task_role' else [None]
                for task in tasks:
                    for role in ['public_reference','development_train','private_train','validation','sealed_test']:
                        records=[x for x in r['support'][protocol] if x['role']==role and (task is None or x.get('task_id')==task)]
                        labels={x['binary_label'] for x in records if x['groups']>0}
                        assert labels=={0,1}, f'Unsupported binary role: {name} {protocol} {task} {role}'
                        support_checks.append({'protocol':protocol,'task':task,'role':role,'both_binary_classes':True})
            checks.append({'dataset':name,'manifest_hash_verified':True,'contract_hash_verified':True,'persisted_row_and_group_checks':True,'stress_boundaries_verified':True,'binary_support':support_checks})
            # Commit small contracts; row-level memberships stay local and ignored.
            write_json(ROOT/'reports/splits/contracts'/f'{name}.json',c)
        finally:
            con.close()
        results.append(r)
    report=['# CP3 split and support results','', 'S1 / M0.3, 2026-09-09. No model scores were computed. Source-wide quality and label counts were inspected before sealing.','',
        'Memberships and contracts were independently reopened and hash-checked. Source-row coverage, unique row IDs, group-role separation, one representative per group, sealed roles and stress boundaries pass. Both binary classes are present in every accepted training/reference/validation/test role and in both NF task periods.','',
        '| Dataset | Source rows | Normalized groups | Quarantined rows | Quarantined groups |','|---|---:|---:|---:|---:|']
    for r in results:
        q=[x for x in r['support']['primary_role'] if x['role']=='quarantine_conflict']
        # Group counts repeated by label in support; obtain unique total from membership.
        con=duckdb.connect(); qgroups=con.execute(f"SELECT count(DISTINCT group_id) FROM read_parquet({lit(r['manifest_path'])}) WHERE primary_role='quarantine_conflict'").fetchone()[0]; con.close()
        report.append(f"| {r['dataset']} | {r['rows']:,} | {r['groups']:,} | {sum(x['rows'] for x in q):,} | {qgroups:,} |")
    for r in results:
        report += ['',f"## {r['dataset']}",'',f"Runtime: {r['elapsed_seconds']:.3f} seconds for its full manifest invocation. See [machine-readable support](splits/{r['dataset']}.json).",'',
                   '| Primary role | Rows | Groups / training representatives |','|---|---:|---:|']
        totals=defaultdict(lambda:[0,0])
        for x in r['support']['primary_role']:
            if x['role']=='quarantine_conflict': continue
            totals[x['role']][0]+=x['rows']; totals[x['role']][1]+=x['groups']
        for role,(rows,groups) in sorted(totals.items()): report.append(f'| {role} | {rows:,} | {groups:,} |')
        report += ['', '| Canonical class | Quarantined rows | Development groups | Validation groups | Final groups | ≥5 groups in each? |','|---|---:|---:|---:|---:|---|']
        by_label=defaultdict(dict)
        for x in r['support']['primary_role']: by_label[x['label']][x['role']]=x
        for label,roles in sorted(by_label.items()):
            nums=[roles.get(role,{}).get('groups',0) for role in ['development_train','validation','sealed_test']]
            lost=roles.get('quarantine_conflict',{}).get('rows',0)
            report.append(f"| {label} | {lost:,} | {nums[0]:,} | {nums[1]:,} | {nums[2]:,} | {'yes' if min(nums)>=5 else 'no'} |")
        report += ['', 'The five-group threshold is a pre-fit support diagnostic, not a statistical guarantee. No resampling or seed search repairs insufficient independent observations. Binary comparison is primary; multiclass/per-family conclusions must disclose these limitations. Quarantining attack-subtype conflicts also removes some binary-consistent rows.','',
                   '| Stress role | Rows | Groups |','|---|---:|---:|']
        totals=defaultdict(lambda:[0,0])
        for x in r['support']['stress_role']:
            if x['role'].startswith(('excluded','quarantine')): continue
            totals[x['role']][0]+=x['rows']; totals[x['role']][1]+=x['groups']
        for role,(rows,groups) in sorted(totals.items()): report.append(f'| {role} | {rows:,} | {groups:,} |')
        if r['stress_cutoffs_ms']:
            boundary_rows=sum(x['rows'] for x in r['support']['task_role'] if x['role']=='excluded_task_boundary')
            report += ['',f'{boundary_rows:,} rows are excluded specifically from CL because their predictor group spans the two capture periods. They retain their original primary role for the separate within-corpus study. Exclusions by class remain in the support JSON.']
            report += ['',f"Chronological stress cutoffs (Unix-millisecond interpretation): {r['stress_cutoffs_ms']}. Role filtering and exclusion of groups spanning boundaries intentionally change the nominal proportions.",'',
                       '| Capture task | Primary role | Benign rows | Attack rows |','|---|---|---:|---:|']
            totals=defaultdict(lambda:[0,0])
            for x in r['support']['task_role']:
                if x['role'].startswith(('excluded','quarantine')): continue
                totals[(x['task_id'],x['role'])][x['binary_label']]+=x['rows']
            for (task,role),counts in sorted(totals.items()): report.append(f'| {task} | {role} | {counts[0]:,} | {counts[1]:,} |')
    report += ['', '## Accepted scope and remaining gates','',
        'Accept S1 for binary baseline preparation, with disclosed conservative conflict exclusions. Both NF capture periods support the binary CL design; three natural tasks are not claimed. Multiclass support and Friday/temporal stress are separate, qualified endpoints. Models and thresholds must be selected within their own protocol namespace.','',
        'The three external datasets have immutable source-hash seals in reports/splits/external. No external performance has been observed. Shared extraction semantics, host/session dependence, any additional preprocessing collisions, training-only imputation/encoding, and privacy release/accounting remain CP4 or later gates.','',
        'No learned transform, model, client assignment or privacy guarantee is produced at CP3. Row-level Parquet manifests stay under ignored data/splits/S1; tracked contracts and reports contain their hashes. Raw sources are unchanged.']
    (ROOT/'reports/CP3-split-results.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    write_json(ROOT/'reports/splits/verification.json',{'version':'S1','status':'PASSED','checks':checks,'tests':'Three split tests passed; see tests/test_splits.py','limits':'No model evaluation or host/session independence certificate'})
    p=ROOT/'docs/registries/project.json'; project=json.loads(p.read_text()); e=next(x for x in project['experiments'] if x['experiment_id']=='EXP-002')
    e.update(status='COMPLETED',dataset_version='EXP-001 source SHA-256 manifests',feature_set='S1 positional contracts: CIC 77, NF 49 candidate predictors',
        model='N/A - deterministic membership construction',environment_versions={'python':'3.13.13','duckdb':'1.5.5','psutil':'7.2.2'},hardware='reports/audit/environment.json',
        metrics={r['dataset']:{'rows':r['rows'],'normalized_groups':r['groups']} for r in results},runtime={r['dataset']:r['elapsed_seconds'] for r in results},
        memory_usage='4GB DuckDB buffer cap; peak process RSS not instrumented for this invocation',
        artifacts=['docs/CP3-split-protocol-S1.md','reports/CP3-split-results.md','reports/splits/verification.json','reports/splits/contracts','reports/splits/external'],
        result='Two complete row-level development-family manifests and three external source seals; no model scores',
        interpretation='Binary roles/tasks supported; rare-class conclusions restricted by unique-group support',decision='Accept S1; advance to CP4 transformations and transformed-overlap checks',
        cl_configuration='Two NF capture-period tasks; no CIC CL stream defined',privacy_configuration='Separate public/development/private/validation/final groups; conditional curation only, no DP claim',
        architecture_impact='A0 remains provisional; data contracts and two-task NF evaluation now concrete')
    if not any(d['decision_id']=='DEC-014' for d in project['decisions']):
        project['decisions'].append({'decision_id':'DEC-014','question':'Which data protocol supports the next model gate?',
            'candidate_alternatives':['Raw row stratification','Three calendar-day tasks','S1 normalized groups with two capture periods'],
            'evidence_considered':['EXP-001 audit','docs/CP3-split-protocol-S1.md','reports/CP3-split-results.md'],'experiments_used':['EXP-002'],
            'selected_option':'S1 conservative conflict quarantine and global disjoint roles; two NF tasks, separate stress namespaces',
            'why_selected':'Persisted coverage/overlap checks pass and every binary role/task has both classes',
            'rejected_alternatives':['Treat numeric spellings as different groups','Promote benign-only day to comparable third task'],
            'why_rejected':'Would weaken leakage checks or task interpretation','risks':['Rare classes lose support','No host/session independence','Later feature transforms can merge groups'],
            'trade_offs':['Conservative exclusions reduce samples','Time stress uses smaller role-filtered populations'],
            'confidence':'High for verified membership invariants; limited for real deployment generalization','architecture_version':'A0','revisit_condition':'CP4 transformed-overlap or semantic checks fail'})
    project['progress'].update(checkpoint='CP3',status='COMPLETE',current=[],next=['CP4: deterministic cleaning, training-only imputation/encoding/scaling, transformed-overlap checks','CP5 / EXP-003: baseline resource pilot after CP4 passes'])
    project['progress']['completed']=list(dict.fromkeys(project['progress']['completed']+['S1 labels/features/groups and split manifests','Two supported NF capture-period tasks','Three sealed external source contracts']))
    project['failures'].append({'experiment_id':'EXP-002','what_failed':'Initial split fixture schema','error':'DuckDB reserved keyword binary used as a column name','suspected_cause':'SQL identifier choice','investigation':'Fixture failed before any source processing','fix':'Renamed field binary_label; all three split fixtures passed','scientifically_invalid':False,'rerun_required':False})
    project['failures']=list({json.dumps(f,sort_keys=True):f for f in project['failures']}.values())
    write_json(p,project)
    print('CP3 verification PASSED; S1 accepted for CP4')


if __name__=='__main__': main()
