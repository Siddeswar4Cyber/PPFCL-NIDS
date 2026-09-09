"""Validate completed audit artifacts and advance the local checkpoint registry."""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]


def save(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')


def main():
    audit=ROOT/'reports/audit'
    families=[]
    errors=[]
    for path in sorted(audit.glob('*.json')):
        record=json.loads(path.read_text(encoding='utf-8'))
        if 'dataset' not in record:
            continue
        families.append(record)
        if record['status']!='COMPLETED':
            errors.append(f"{record['dataset']} is not complete")
            continue
        if sum(p['rows'] for p in record['file_profiles'])!=record['rows']:
            errors.append(f"{record['dataset']}: row/profile disagreement")
        if sum(r['rows'] for r in record['label_counts'])!=record['rows']:
            errors.append(f"{record['dataset']}: row/label disagreement")
        for f in record['files']:
            p=next(p for p in record['file_profiles'] if p['source_file']==f['source_file'])
            if f['physical_lines']!=p['rows']+1+f['parsing']['rejected_physical_line_locations']:
                errors.append(f"Physical/parsed count discrepancy needs investigation: {f['path']}")
            for c in p['columns']:
                counts=[c[k] for k in ['blank','nan','positive_infinity','negative_infinity','finite','non_numeric_nonblank']]
                if any(not isinstance(v,int) or v<0 for v in counts) or sum(counts)!=p['rows']:
                    errors.append(f"Column quality counts do not partition rows: {f['path']} {c['id']}")
    if len(families)!=5:
        errors.append(f'Expected five families, found {len(families)}')
    run=json.loads((audit/'run.json').read_text())
    if not run['all_requested_families_completed']:
        errors.append('Runner did not finish requested scope')
    provenance=json.loads((audit/'archive-provenance.json').read_text())
    if not all(c['matches'] for a in provenance['archives'] for c in a['checks']):
        errors.append('Local archive manifest mismatch')
    total=sum(f.get('rows',0) for f in families)
    verification={'recorded_utc':datetime.now(timezone.utc).isoformat(),'families':len(families),'source_csvs':sum(len(f['files']) for f in families),'total_rows':total,'errors':errors,'tests':'Four constructed-fixture integration tests; see tests/test_audit.py','limits':'No classifier training, host-independent split proof or numeric-normalized duplicate equivalence.'}
    save(audit/'verification.json',verification)
    if errors:
        raise SystemExit('\n'.join(errors))
    project_path=ROOT/'docs/registries/project.json'
    project=json.loads(project_path.read_text())
    exp=next(e for e in project['experiments'] if e['experiment_id']=='EXP-001')
    exp.update(status='COMPLETED',date='2026-09-09',dataset_version='Source SHA-256 manifests in reports/audit/*.json',split_version='N/A - no split fitted',feature_set='All source columns, positional IDs retained',model='N/A - audit',hyperparameters={'audit_versions':['audit-1.0','audit-1.1','audit-1.2','audit-1.3'],'duckdb_memory_limit':'4GB','threads_last_run':8},seed=None,client_configuration='N/A',privacy_configuration='Public benchmark audit outside private-training boundary',cl_configuration='N/A',environment_versions={'python':'3.13.13','duckdb':'1.5.5','psutil':'7.2.2'},preprocessing_version='N/A - diagnostics only',metrics={'audited_rows':total,'dataset_families':5,'source_csvs':verification['source_csvs']},runtime={'family_runtime':{f['dataset']:{'seconds':f['elapsed_seconds'],'scope':f.get('elapsed_scope','Full family invocation'),'phase_timings':f.get('stage_timings')} for f in families},'latest_invocation_seconds':run['elapsed_seconds'],'note':'Earlier interrupted attempts are not included in latest invocation runtime.'},memory_usage={'latest_invocation_peak_rss_bytes':run['peak_process_rss_bytes'],'note':'Earlier v1.0 run observed 6.28 GiB RSS; whole-session peak was not persisted.'},artifacts=['reports/CP1-dataset-audit.md','reports/CP1-findings-and-decisions.md','reports/audit/verification.json','reports/audit/environment.json','reports/audit/archive-provenance.json'],logs=['reports/audit-console.log','reports/audit-console-v1.1.log','reports/audit-console-v1.2.log','reports/audit-errors-v1.2.log','reports/audit-console-v1.3.log'],result='Read-only audit completed for five local families; no model results.',interpretation='Duplicate, label, nonfinite-value and temporal findings require explicit preprocessing/split decisions.',decision='Advance to split and preprocessing protocol gate; retain raw data.',architecture_impact='A0 retained as provisional; no empirical model winner selected.')
    project['updated']='2026-09-09'
    progress=project['progress']
    progress.update(checkpoint='CP2',status='COMPLETE',current=[],next=['CP3 / EXP-002: finalize split/task/feature manifests and quarantine policy','CP4: implement deterministic cleaning and fit training-only transforms','CP5: resource pilot and controlled baselines'])
    progress['completed'] += ['Isolated pinned audit environment','Full row audit of five datasets','Four correctness tests and artifact invariants','Local ZIP manifest consistency checks']
    progress['completed']=list(dict.fromkeys(progress['completed']))
    progress['needs_validation']=['Numeric-normalized duplicates after proposed transformations','Cleaning impact on minority support','Split independence and task support','All detection, FL, privacy and CL results','Training-framework CUDA support']
    project['user_constraints']['hardware_measured']='reports/audit/environment.json; psutil RAM differs from earlier user-reported value'
    project['failures'] += [
        {'experiment_id':'EXP-001','what_failed':'Fixture parser initialization','error':'Empty nullstr list rejected by DuckDB 1.5.5','suspected_cause':'Unsupported option value','investigation':'Constructed fixture failed before data audit','fix':'Explicit force_not_null for all positional columns','scientifically_invalid':False,'rerun_required':False},
        {'experiment_id':'EXP-001','what_failed':'Initial complete-scope attempts interrupted','error':'v1.0 intentionally stopped for measured optimization; v1.1 and v1.2 processes ended before remaining stages completed','suspected_cause':'Intentional optimization for v1.0; later process termination cause not established','investigation':'Completed family artifacts retained; no surviving foreground audit process','fix':'Resume with full source hash checks and v1.3 staged recovery; all families eventually completed','scientifically_invalid':False,'rerun_required':False}]
    decision_id='DEC-013'
    if not any(d['decision_id']==decision_id for d in project['decisions']):
        project['decisions'].append({'decision_id':decision_id,'question':'Can raw rows be split and fitted without a data-quality policy?','candidate_alternatives':['Naive row split','Group-aware split after explicit audit-derived rules'],'evidence_considered':['reports/CP1-dataset-audit.md','reports/CP1-findings-and-decisions.md'],'experiments_used':['EXP-001'],'selected_option':'Register cleaning, duplicate grouping and temporal rules before any fit','why_selected':'Actual duplicates, conflicting-label features and rate/time issues were observed','rejected_alternatives':['Treat file order as time','Keep both identical CIC Fwd Header Length columns','Assume valid UTF-8 means undamaged labels'],'why_rejected':'Contradicted by local audit observations','risks':['Rare classes may lose support','Predictor collisions are not necessarily duplicate events'],'trade_offs':['Stricter evaluation may reduce scores or available samples'],'confidence':'High for observed anomalies; split design remains provisional','architecture_version':'A0','revisit_condition':'EXP-002 support and normalized-overlap checks'})
    project['failures']=list({json.dumps(f,sort_keys=True):f for f in project['failures']}.values())
    save(project_path,project)
    print(json.dumps(verification,indent=2))


if __name__=='__main__':
    main()
