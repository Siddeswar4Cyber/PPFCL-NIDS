"""Verify saved validation predictions and summarize the bounded B1 pilot."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from audit_datasets import write_json
from preprocess_p1 import sha
from baseline_metrics import evaluate,threshold_for_fpr
from run_baseline_pilot import DATASETS,PROTOCOLS,MODELS,bundle,identity,load_partition

ROOT=Path(__file__).resolve().parents[1]


def main():
    runs=[]; checks=[]
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            version,pipe,params=bundle(dataset,protocol)
            _,y,labels=load_partition(dataset,protocol,'validation',pipe,len(params['output_names']),features=False)
            universe=sorted(set(json.loads((ROOT/'reports/splits/contracts'/f'{dataset}.json').read_text())['raw_to_canonical_label'].values()))
            for kind in MODELS:
                run_id=identity(dataset,protocol,kind); r=json.loads((ROOT/'reports/baselines/runs'/f'{run_id}.json').read_text())
                assert r['status']=='COMPLETED' and r['exit_code']==0 and r['resource_limit_stop'] is None
                assert r['script_sha256']==sha(ROOT/'scripts/run_baseline_pilot.py') and r['metrics_script_sha256']==sha(ROOT/'scripts/baseline_metrics.py')
                assert r['preprocessing_version']==version and r['transform_sha256']==pipe['transform_sha256']
                assert r['fit_group_set_sha256']==pipe['fit_group_set_sha256'] and r['input_artifacts']==pipe['artifacts']
                assert r['train_rows']==100000 and r['validation_rows']==len(y)
                assert not r['final_test_accessed'] and not r['external_test_accessed']
                assert r['sampled_peak_process_rss_bytes']<12*2**30 and r['supervised_wall_seconds']<600
                assert sha(r['model_artifact']['path'])==r['model_artifact']['sha256'] and sha(r['validation_predictions']['path'])==r['validation_predictions']['sha256']
                p=np.load(r['validation_predictions']['path'],allow_pickle=False)
                assert r['metrics_05']==evaluate(y,p,labels,universe,0.5)
                threshold=threshold_for_fpr(y,p)
                assert r['metrics_fpr01']==evaluate(y,p,labels,universe,threshold)
                assert r['metrics_fpr01']['confusion']['fp']<=int(0.01*int((y==0).sum()))
                if kind=='prior':
                    assert np.max(p)==np.min(p) and r['metrics_05']['attack_recall']==0
                    assert abs(r['metrics_05']['average_precision']-float(y.mean()))<1e-12
                runs.append(r); checks.append({'run_id':run_id,'saved_metric_recomputation':'PASSED','input_and_model_hashes':'PASSED','same_scope_training_population':'PASSED','resource_limits':'PASSED','final_external_access':False})
    write_json(ROOT/'reports/baselines/verification.json',{'version':'B1','status':'PASSED','runs':len(runs),'checks':checks,'limits':'Validation-only, one fixed configuration and seed per model/namespace; no generalization or privacy guarantee'})
    p2=json.loads((ROOT/'reports/preprocessing/cic-ids-2017-P2.json').read_text())
    lines=['# CP5 CPU baseline pilot results','', 'B1 / M0.5, 2026-09-09. These are selection-validation results, not final-test or external-domain scores. All 16 fixed-budget runs completed and their saved probabilities reproduce the recorded metrics. Each model trained on the exact 100,000 representatives for its namespace.','',
        '## Data amendment before the first model fit','',
        f"P1's CIC float32 conversion merged 22,813 vectors and implicated {p2['excluded_groups']:,} S1 groups. P2 conservatively excludes all {sum(x['rows'] for x in p2['exclusion_support']):,} associated rows, preserves S1 roles, refits preprocessing, and passes both precision gates. All CIC candidates below use P2; NF uses P1. P1's earlier data counts and raw-dataset literature scores are not directly comparable with this population.",'',
        '| CIC class | P2 precision-excluded rows |','|---|---:|']
    excluded=defaultdict(int)
    for x in p2['exclusion_support']: excluded[x['label']]+=x['rows']
    for label,n in sorted(excluded.items()): lines.append(f'| {label} | {n:,} |')
    lines += ['', '## Validation comparisons','', 'AP denotes average precision. Macro-F1, attack F1 and FPR below use threshold 0.5. Recall@1% uses a separately validation-calibrated threshold; its empirical FPR is at most 1%, not necessarily exactly 1%. No confidence interval or seed-averaged ranking is claimed.']
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            chosen=[r for r in runs if r['dataset']==dataset and r['protocol']==protocol]
            lines += ['',f'### {dataset} / {protocol}', '',f"Validation rows: {chosen[0]['validation_rows']:,}. Attack prevalence: {chosen[0]['metrics_05']['attack_prevalence']:.4%}.",'',
                '| Model | Macro-F1 | Attack F1 | AP | FPR | Recall@1% | Fit seconds | Model KiB | RSS GiB |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
            for r in chosen:
                m=r['metrics_05']; c=r['metrics_fpr01']
                lines.append(f"| {r['model_kind']} | {m['binary_macro_f1']:.6f} | {m['attack_f1']:.6f} | {m['average_precision']:.6f} | {m['benign_fpr']:.6f} | {c['attack_recall']:.6f} | {r['fit_seconds']:.3f} | {r['model_artifact']['bytes']/1024:.1f} | {r['sampled_peak_process_rss_bytes']/2**30:.3f} |")
            winner=max((r for r in chosen if r['model_kind']!='prior'),key=lambda r:r['metrics_05']['binary_macro_f1'])
            lines += ['',f"Highest observed macro-F1 in this fixed pilot: {winner['model_kind']}. This is a provisional ranking for this namespace only. Stress rows are the stress protocol's permitted validation population, not its sealed held-out Friday/final-time test."]
    lines += ['', '## Interpretation and next comparisons','',
        'The dummy baseline demonstrates why high accuracy under class imbalance is insufficient: it detects no attacks. Trained candidates improve substantially, but the very high NF validation scores require scrutiny of capture/host dependence and shortcut features. Input hashes, label-column exclusion and exact group separation pass; these checks do not prove independent real-world events or causal attack learning.','',
        'Retain the strongest classical candidates as baselines and the compact MLP as an integration candidate. No final detector, FL method, privacy budget or continual-learning method is selected. Numeric protocol/port encoding, feature ablations, training-only feature selection and repeat seeds remain EXP-003 work. Any feature reduction or dtype change requires a renewed overlap gate and a common population for compared methods.','',
        'Only one setting and seed 17 were tested per model. MLP uses the final bounded epoch, without automatic validation splitting or best-epoch selection. Convergence warnings and actual iterations are retained below. Near-perfect NF results are source-corpus evidence only; external data and final tests remain sealed.','',
        '## Convergence and cost details','', '| Run | Iterations/epochs | Warnings | Prediction seconds | Warm batch p50/p95 ms |','|---|---|---|---:|---|']
    for r in runs:
        lines.append(f"| {r['run_id']} | {r['iterations']} | {', '.join(w['category'] for w in r['warnings']) or 'none'} | {r['validation_prediction_seconds']:.3f} | {r['latency']['batch_p50_ms']:.3f} / {r['latency']['batch_p95_ms']:.3f} |")
    lines += ['', 'Latencies are warmed 4,096-row prediction batches (seven repetitions), not per-flow end-to-end detection delay. Model bytes are compressed joblib artifacts. RSS is the sampled sum over the worker process tree, including the Windows launcher; it is not a GPU measurement.','',
        'The first tree worker exposed a NumPy-integer JSON serialization bug. The initial supervisor also sampled only the Windows launcher. Those attempts are retained under reports/baselines/initial-attempt and models/B1-initial-attempt, with actual worker RSS marked unavailable. After fixing serialization and process-tree monitoring, all configurations were rerun unchanged. Initial attempts are not independent confirmation seeds and are not pooled into the tables.','',
        'The source/configuration and P2 gate were preregistered in local commit 3d31e90 before the first model fit. Exact current code, data, transform, model and probability hashes are recorded per run. See [verification](baselines/verification.json) and [protocol](../docs/CP5-baseline-protocol-B1.md).']
    (ROOT/'reports/CP5-baseline-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    path=ROOT/'docs/registries/project.json'; project=json.loads(path.read_text()); e=next(x for x in project['experiments'] if x['experiment_id']=='EXP-003')
    e.update(status='RUNNING',metrics={'B1_completed_runs':16,'confirmation_seeds_completed':0},runtime={'successful_worker_fit_seconds':sum(r['fit_seconds'] for r in runs),'successful_supervised_seconds':sum(r['supervised_wall_seconds'] for r in runs),'initial_attempts_additional':True},
        environment_versions=runs[0]['environment'],hardware='reports/audit/environment.json',artifacts=['reports/CP5-baseline-results.md','reports/baselines/verification.json','reports/baselines/runs'],logs=['reports/baseline-console-B1.log'],
        result='B1 pilot complete: 16 validation-only prior/LR/tree/MLP runs; no final-test results',interpretation='Initial feasibility and ranking evidence; feature/model selection and confirmation remain outstanding',
        decision='Advance to CP6 controlled feature/encoding comparisons and repeat seeds before FL integration',architecture_impact='Centralized pilot components implemented; A0 candidate methods remain provisional')
    e.update(dataset_version='Audited CIC-IDS2017 P2 and NF-UNSW-NB15-v3 P1; source SHA-256 bindings in S1 contracts',
        feature_set='CIC: 77 numeric, 77 missing and 2 sentinel fields (156); NF: 49 numeric and 49 missing fields (98)',
        client_configuration='Centralized CPU pilot; no federation',
        privacy_configuration='Non-private development pilot; private preprocessing and DP accounting pending',
        cl_configuration='No CL model run at B1; task manifests remain preparatory',
        memory_usage={'max_sampled_worker_process_tree_rss_bytes':max(r['sampled_peak_process_rss_bytes'] for r in runs),'measurement':'Sum over worker and descendants, sampled every 0.5 seconds'},
        dependency_lock='requirements-baseline.txt')
    architecture=next(a for a in project['architectures'] if a['version']=='A0')
    architecture['supporting_experiments']=list(dict.fromkeys(architecture['supporting_experiments']+['EXP-003']))
    architecture['supporting_decisions']=list(dict.fromkeys(architecture['supporting_decisions']+['DEC-015','DEC-016','DEC-017']))
    architecture['status']='PROVISIONAL / DATA PIPELINE AND CENTRALIZED PILOT IMPLEMENTED'
    architecture['known_limitations']=['FL/DP/CL algorithms remain unimplemented and unselected',
        'No established privacy guarantee', 'Group separation verified; event/host independence not established',
        'B1 evidence is fixed-budget, single-seed validation only; EXP-003 selection remains in progress',
        'One-laptop simulation; no banking data']
    for r in runs:
        entry={**r,'date':'2026-09-09','architecture_version':'A0','client_configuration':'Centralized CPU pilot; no federation','privacy_configuration':'Non-private development only','cl_configuration':'No CL model run at B1','result':'Validation pilot complete; no final/external score','interpretation':'Single seed and fixed budget; not a final winner'}
        project['runs']=[x for x in project['runs'] if x['run_id']!=entry['run_id']]+[entry]
    decisions=[('DEC-016','Can P1 float32 tree inputs reuse CIC S1 without amendment?','P2 excludes all precision-colliding groups before model scores and refits all CIC candidates','Float32 merged groups across reserved roles; P2 resolves both precision gates','Conservative exclusion changes the evaluated population'),
               ('DEC-017','Does B1 select a final detector or integration stack?','Retain classical baselines and MLP candidate; continue controlled EXP-003 comparisons','All fixed-budget candidates are feasible, but evidence is one seed and validation only','Very high source-corpus scores may exploit capture shortcuts')]
    for did,question,choice,why,risk in decisions:
        if not any(d['decision_id']==did for d in project['decisions']): project['decisions'].append({'decision_id':did,'question':question,'candidate_alternatives':['Ignore limitation and proceed to final claims',choice],'evidence_considered':['reports/CP5-baseline-results.md','docs/CP5-baseline-protocol-B1.md'],'experiments_used':['EXP-003'],'selected_option':choice,'why_selected':why,'rejected_alternatives':['Unqualified winner/generalization claim'],'why_rejected':'Not supported by this gate','risks':[risk],'trade_offs':['More controlled comparisons are required'],'confidence':'High for measured pilot; limited for deployment generalization','architecture_version':'A0','revisit_condition':'CP6 comparison and confirmation evidence'})
    project['failures'] += [
        {'experiment_id':'EXP-003','what_failed':'P1 CIC float32 equality gate','error':'22813 merged vectors; 16892 crossed primary roles','suspected_cause':'Finite-precision collapse','investigation':'All admitted groups checked before model scores','fix':'P2 excludes implicated groups and refits every CIC pipeline','scientifically_invalid':False,'rerun_required':False},
        {'experiment_id':'EXP-003','what_failed':'Initial worker reporting and RAM monitoring','error':'NumPy tree-size integer not JSON-serializable; launcher-only RSS sampled','suspected_cause':'NumPy scalar type and Windows venv launcher topology','investigation':'Preserved original logs and artifacts; actual worker RSS unavailable for initial attempts','fix':'Native integer serialization, process-tree monitoring, unchanged-config rerun','scientifically_invalid':False,'rerun_required':False}]
    project['failures']=list({json.dumps(f,sort_keys=True):f for f in project['failures']}.values())
    project['progress'].update(checkpoint='CP5',status='COMPLETE',current=[],next=['CP6 / EXP-003: shortcut/feature/encoding comparisons under renewed overlap controls','Confirm retained configurations across seeds 17,29,43 before final selection','Then client partitioning and FL comparisons'])
    project['progress']['completed']=list(dict.fromkeys(project['progress']['completed']+['P2 CIC precision amendment','B1 16-run CPU baseline pilot and saved-prediction verification']))
    project['progress']['needs_validation']=['Feature/encoding/model comparison and repeat seeds','Capture/host shortcuts and grouping limitations','CL/GPU-specific precision and implementation equivalence','Private preprocessing and DP release accounting','External transformed overlap and final evaluation','All FL and CL comparative results']
    write_json(path,project)
    print('CP5 B1 verification PASSED: 16 runs; EXP-003 remains in progress')


if __name__=='__main__': main()
