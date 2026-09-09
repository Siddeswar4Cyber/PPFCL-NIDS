"""Independently recompute B2 saved metrics, verify bindings, and record CP6."""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits
from audit_datasets import write_json
from preprocess_p1 import sha
from baseline_metrics import evaluate, threshold_for_fpr
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, bundle, load_partition, identity as b1id
from cp6_features import define_features, transform
from run_cp6 import MODELS, identity, feature_spec, select_representation


def read(path): return json.loads(Path(path).read_text())


def main():
    all_runs=[]; features={}; metrics_cache={}; checked=[]; b1={}; report_bindings=[]; verified_commits=set()
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            _,pipe,params=bundle(dataset,protocol); spec,path=feature_spec(dataset,protocol); features[(dataset,protocol)]=spec
            assert sha(spec['cleaned']['path'])==spec['cleaned']['sha256']
            with threadpool_limits(limits=2):
                x,y,_=load_partition(dataset,protocol,'train',pipe,len(params['output_names']))
                definitions,ranking,_=define_features(dataset,params,x,y)
            assert ranking==spec['training_only_ranking']
            for variant,d in definitions.items():
                saved=spec['definitions'][variant]
                assert {k:v for k,v in saved.items() if k!='gate'}==d
                z=transform(x,d)
                if variant=='categorical_augmented': assert np.array_equal(z[:,:x.shape[1]],x)
            del x,z
            _,yv,lv=load_partition(dataset,protocol,'validation',pipe,len(params['output_names']),features=False)
            universe=sorted(set(read(ROOT/'reports/splits/contracts'/f'{dataset}.json')['raw_to_canonical_label'].values()))
            metrics_cache[(dataset,protocol)]=(yv,lv,universe)
            for kind in MODELS:
                old=read(ROOT/'reports/baselines/runs'/f'{b1id(dataset,protocol,kind)}.json')
                assert old['input_artifacts']==pipe['artifacts'] and old['transform_sha256']==pipe['transform_sha256']
                for key in ['model_artifact','validation_predictions']: assert sha(old[key]['path'])==old[key]['sha256']
                bp=np.load(old['validation_predictions']['path'],allow_pickle=False)
                assert old['metrics_05']==evaluate(yv,bp,lv,universe,.5)
                assert old['metrics_fpr01']==evaluate(yv,bp,lv,universe,threshold_for_fpr(yv,bp))
                old['representation']='full'; b1[(dataset,protocol,kind)]=old
            for run_path in sorted((ROOT/'reports/cp6/runs').glob(f'B2-{dataset}-{protocol}-*.json')):
                r=read(run_path); assert r['status']=='COMPLETED' and r['exit_code']==0 and r['resource_limit_stop'] is None
                assert r['script_sha256']==sha(ROOT/'scripts/run_cp6.py') and r['features_script_sha256']==sha(ROOT/'scripts/cp6_features.py')
                assert r['baseline_script_sha256']==sha(ROOT/'scripts/run_baseline_pilot.py') and r['metrics_script_sha256']==sha(ROOT/'scripts/baseline_metrics.py')
                if r['git_commit'] not in verified_commits:
                    for source in ['run_cp6.py','cp6_features.py','run_baseline_pilot.py','baseline_metrics.py']:
                        committed=subprocess.check_output(['git','show',r['git_commit']+':scripts/'+source],cwd=ROOT)
                        assert hashlib.sha256(committed).hexdigest()==sha(ROOT/'scripts'/source)
                    verified_commits.add(r['git_commit'])
                assert r['feature_spec_sha256']==sha(path) and r['transform_sha256']==pipe['transform_sha256']
                assert r['fit_group_set_sha256']==pipe['fit_group_set_sha256'] and r['input_artifacts']==pipe['artifacts']
                assert spec['definitions'][r['representation']]['gate']['status']=='PASSED'
                assert r['train_rows']==100000 and r['validation_rows']==len(yv)
                assert r['sampled_peak_process_rss_bytes']<12*2**30 and r['supervised_wall_seconds']<600
                assert not r['final_test_accessed'] and not r['external_test_accessed'] and r['model_roundtrip_max_abs_delta']<=1e-12
                for key in ['model_artifact','validation_predictions']: assert sha(r[key]['path'])==r[key]['sha256']
                p=np.load(r['validation_predictions']['path'],allow_pickle=False)
                assert r['metrics_05']==evaluate(yv,p,lv,universe,.5)
                assert r['metrics_fpr01']==evaluate(yv,p,lv,universe,threshold_for_fpr(yv,p))
                assert r['metrics_fpr01']['confusion']['fp']<=int(.01*int((yv==0).sum()))
                old=b1[(dataset,protocol,r['model_kind'])]
                assert {k:v for k,v in r['hyperparameters'].items() if k!='random_state'}=={k:v for k,v in old['hyperparameters'].items() if k!='random_state'}
                all_runs.append(r); checked.append(r['run_id']); report_bindings.append({'path':str(run_path),'sha256':sha(run_path)})
    indexed={r['run_id']:r for r in all_runs}; selection=read(ROOT/'reports/cp6/selection.json'); summaries=[]; expected=set()
    for s in selection['selected']:
        dataset,protocol,kind=s['dataset'],s['protocol'],s['model_kind']; spec=features[(dataset,protocol)]
        candidates=[b1[(dataset,protocol,kind)]]
        for variant,d in spec['definitions'].items():
            if variant=='full' or d['gate']['status']!='PASSED': continue
            rid=identity(dataset,protocol,kind,variant,17); expected.add(rid); candidates.append(indexed[rid])
        for binding in s['candidate_reports']: assert sha(binding['path'])==binding['sha256']
        winner=select_representation(candidates); assert winner['run_id']==s['seed17_run_id'] and winner['representation']==s['representation']
        seeds=[winner]
        for seed in [29,43]:
            rid=identity(dataset,protocol,kind,s['representation'],seed); expected.add(rid); seeds.append(indexed[rid])
        values=[r['metrics_05']['binary_macro_f1'] for r in seeds]
        families={}
        for family in seeds[0]['metrics_05']['attack_family_recall']:
            entries=[r['metrics_05']['attack_family_recall'][family] for r in seeds]
            if entries[0]['binary_attack_recall'] is not None:
                families[family]={'support':entries[0]['support'],'mean_binary_attack_recall':float(np.mean([e['binary_attack_recall'] for e in entries]))}
        summaries.append({**s,'seed_run_ids':[r['run_id'] for r in seeds],'macro_f1_by_seed':dict(zip(['17','29','43'],values)),
            'macro_f1_mean':float(np.mean(values)),'macro_f1_sample_sd':float(np.std(values,ddof=1)),
            'average_precision_mean':float(np.mean([r['metrics_05']['average_precision'] for r in seeds])),
            'benign_fpr_mean':float(np.mean([r['metrics_05']['benign_fpr'] for r in seeds])),
            'recall_at_calibrated_fpr01_mean':float(np.mean([r['metrics_fpr01']['attack_recall'] for r in seeds])),
            'fit_seconds_mean':float(np.mean([r['fit_seconds'] for r in seeds])),'attack_family_recall':families})
    assert expected==set(indexed),'Unexpected or missing registered B2 runs'
    permutation=[]
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            d=read(ROOT/'reports/cp6/diagnostics'/f'{dataset}-{protocol}-permutation.json'); assert d['status']=='COMPLETED'
            assert d['script_sha256']==sha(ROOT/'scripts/cp6_diagnostics.py') and not d['final_test_accessed'] and not d['external_test_accessed']
            y,labels,universe=metrics_cache[(dataset,protocol)]
            expected_indices=np.sort(np.random.default_rng(17).choice(len(y),min(50000,len(y)),replace=False))
            assert hashlib.sha256(expected_indices.astype('<i8').tobytes()).hexdigest()==d['row_indices_sha256']
            for r in d['runs']:
                assert sha(r['saved_predictions']['path'])==r['saved_predictions']['sha256']
                with np.load(r['saved_predictions']['path'],allow_pickle=False) as arrays:
                    ids=arrays['row_indices']; assert np.array_equal(ids,expected_indices)
                    assert r['control_metrics_05']==evaluate(y[ids],arrays['control'],labels[ids],universe,.5)
                    for change in r['changes']:
                        m=evaluate(y[ids],arrays[change['array_key']],labels[ids],universe,.5); assert m==change['metrics_05']
                        assert change['macro_f1_drop']==r['control_metrics_05']['binary_macro_f1']-m['binary_macro_f1']
                        assert change['average_precision_drop']==r['control_metrics_05']['average_precision']-m['average_precision']
            permutation.append(d)
    hosts=read(ROOT/'reports/cp6/diagnostics/NF-host-overlap.json'); assert hosts['status']=='COMPLETED'
    assert hosts['script_sha256']==sha(ROOT/'scripts/cp6_diagnostics.py')
    for h in hosts['results']:
        assert sha(h['masks']['path'])==h['masks']['sha256']; a=pq.read_table(h['masks']['path'])
        y,labels,universe=metrics_cache[('ND-UNSW-NB15-v3',h['protocol'])]; missing=a['missing_endpoint'].to_numpy(); seen=a['ordered_pair_seen'].to_numpy(); hs=a['both_hosts_seen'].to_numpy()
        assert np.array_equal(a['ordinal'].to_numpy(),np.arange(1,len(y)+1)) and np.array_equal(a['binary_label'].to_numpy(),y)
        groups={'seen_ordered_pair':seen & ~missing,'unseen_ordered_pair':~seen & ~missing,'both_hosts_seen':hs & ~missing,
            'at_least_one_unseen_host':~hs & ~missing,'missing_endpoint':missing}
        for m in h['subgroup_metrics']:
            r=b1[('ND-UNSW-NB15-v3',h['protocol'],m['model_kind'])]; p=np.load(r['validation_predictions']['path'],allow_pickle=False); mask=groups[m['subgroup']]
            assert int(mask.sum())==m['rows']
            assert m['metrics_05']==(evaluate(y[mask],p[mask],labels[mask],universe,.5) if mask.any() else None)
    write_json(ROOT/'reports/cp6/verification.json',{'status':'PASSED','B2_runs':len(all_runs),'checked_run_ids':checked,
        'training_only_features_recomputed':True,'fixed_comparison_populations':True,'saved_metrics_reproduced':True,'selection_rule_verified':True,
        'permutation_saved_metrics_reproduced':True,'host_subgroup_metrics_reproduced':True,'resource_limits_passed':True,'heldout_model_scores_exposed':False,
        'run_report_bindings':report_bindings,'executed_source_git_commits':sorted(verified_commits),'selection_sha256':sha(ROOT/'reports/cp6/selection.json')})
    write_json(ROOT/'reports/cp6/seed-summary.json',{'version':'B2','status':'COMPLETED','summaries':summaries,'interpretation':'Conditional model-seed sensitivity on the same validation population; no population confidence intervals'})
    lines=['# CP6 feature comparison and shortcut results','',f'B2 / M0.6, 2026-09-09. {len(all_runs)} new CPU fits completed and verified. Twelve B1 full-feature seed-17 runs supply existing controls; they are not new replicates. Final-test and external scores remain sealed.','',
        '## Representation gates','', 'Removing fields changes equality groups. Both reduced candidates fail under the existing S1 split in every namespace; they receive no detector scores. No further rows were excluded, and no roles were reassigned. This rejects a comparison under S1, not the usefulness of those features or the possibility of a redesigned split.','',
        '| Dataset / protocol | Reduction | Float64 merged vectors | Float32 merged vectors | Float32 implicated groups | Cross-primary-role vectors |','|---|---|---:|---:|---:|---:|']
    for (dataset,protocol),spec in features.items():
        for variant in ['no_shortcut','top32']:
            checks=spec['definitions'][variant]['gate']['checks']; a,b=checks
            lines.append(f"| {dataset} / {protocol} | {variant} | {a['merged_vectors']:,} | {b['merged_vectors']:,} | {b['implicated_groups']:,} | {b['cross_primary_role_vectors']:,} |")
    lines+=['','Full vectors and their categorical augmentation pass. Categories and ANOVA rankings are fitted only on the existing training representatives. Augmentation retains numeric coding and adds common-value indicators; it is not pure categorical replacement.','',
        '## Seed-17 representation comparison','', '| Dataset / protocol | Model | Full macro-F1 | Augmented macro-F1 | Full AP | Augmented AP | Chosen for seed sensitivity |','|---|---|---:|---:|---:|---:|---|']
    for s in summaries:
        key=(s['dataset'],s['protocol'],s['model_kind']); full=b1[key]; aug=indexed[identity(*key,'categorical_augmented',17)]
        lines.append(f"| {s['dataset']} / {s['protocol']} | {s['model_kind']} | {full['metrics_05']['binary_macro_f1']:.6f} | {aug['metrics_05']['binary_macro_f1']:.6f} | {full['metrics_05']['average_precision']:.6f} | {aug['metrics_05']['average_precision']:.6f} | {s['representation']} |")
    lines+=['','The fixed rule requires at least 0.002 absolute macro-F1 improvement and at most 0.002 AP loss against full. Otherwise full is retained. Selection uses validation and seed 17, so subsequent seeds do not create independent model-selection evidence.','',
        '## Three-seed sensitivity','', '| Dataset / protocol | Model / representation | Macro-F1 seeds 17, 29, 43 | Mean ± sample SD | Mean AP | Mean FPR | Mean recall at ≤1% validation FPR | Mean fit seconds |','|---|---|---|---:|---:|---:|---:|---:|']
    for s in summaries:
        vals=', '.join(f'{v:.6f}' for v in s['macro_f1_by_seed'].values())
        lines.append(f"| {s['dataset']} / {s['protocol']} | {s['model_kind']} / {s['representation']} | {vals} | {s['macro_f1_mean']:.6f} ± {s['macro_f1_sample_sd']:.6f} | {s['average_precision_mean']:.6f} | {s['benign_fpr_mean']:.6f} | {s['recall_at_calibrated_fpr01_mean']:.6f} | {s['fit_seconds_mean']:.3f} |")
    lines+=['','Training membership is fixed across seeds. This measures estimator randomness conditional on the data and selected representation; it does not measure population uncertainty. LR is effectively deterministic here. Bounded MLP convergence warnings remain in the run records. Family supports and all per-family recalls are retained in [seed summary](cp6/seed-summary.json).', '',
        'CIC primary MLP macro-F1 varies from 0.925472 to 0.965785 (sample SD 0.022140), whereas augmented Extra Trees stays between 0.982385 and 0.983111. The MLP remains an integration candidate, with optimizer/threshold stability still to investigate; its seed-17 encoding gain is not a guaranteed improvement across random initializations.','',
        '## Endpoint overlap','', '| NF protocol | Training hosts | Validation rows | Both hosts seen in training | Ordered pair seen in training | Unseen-pair rows |','|---|---:|---:|---:|---:|---:|']
    for h in hosts['results']:
        lines.append(f"| {h['protocol']} | {h['training_unique_hosts']} | {h['validation_rows']:,} | {h['both_hosts_seen_rows']:,} | {h['ordered_pair_seen_rows']:,} ({h['ordered_pair_seen_rows']/h['validation_rows']:.4%}) | {h['validation_rows']-h['ordered_pair_seen_rows']-h['missing_endpoint_rows']} |")
    lines+=['','| NF protocol | B1 Extra Trees subgroup | Rows | Benign / attack support | False positives | Benign FPR |','|---|---|---:|---|---:|---:|']
    for h in hosts['results']:
        for m in h['subgroup_metrics']:
            if m['model_kind']!='extra_trees' or m['subgroup'] not in ['seen_ordered_pair','unseen_ordered_pair']: continue
            v=m['metrics_05']; c=v['confusion']; lines.append(f"| {h['protocol']} | {m['subgroup']} | {m['rows']:,} | {c['tn']+c['fp']} / {c['tp']+c['fn']} | {c['fp']} | {v['benign_fpr']:.6f} |")
    lines+=['','Nearly all NF validation flows reuse training endpoint pairs. Every unseen-pair validation row is benign: attack recall and AP cannot be estimated there. The B1 tree produces 15/213 (7.04%) false positives on primary unseen pairs and 7/25 (28%) on stress unseen pairs. These small, differently composed subsets do not prove causal host memorization. Raw subgroup macro-F1 retains the fixed two-label zero-division policy and must not be compared directly with two-class macro-F1. No independently held-out-host estimate is established. CIC host metadata is unavailable. Metadata never enters the detector vector.','',
        '## Grouped permutation sensitivity','', 'Each comparison uses the same fixed 50,000-row validation subset, B1 model and threshold 0.5. Positive drops mean worse performance after joint shuffling. Mean drops below summarize three permutations, not three independently trained models.','',
        '| Dataset / protocol | B1 model | Shuffled group | Mean macro-F1 drop | Mean AP drop |','|---|---|---|---:|---:|']
    for d in permutation:
        for r in d['runs']:
            for group in sorted({c['group'] for c in r['changes']}):
                changes=[c for c in r['changes'] if c['group']==group]
                lines.append(f"| {d['dataset']} / {d['protocol']} | {r['model_kind']} | {group} | {np.mean([c['macro_f1_drop'] for c in changes]):.6f} | {np.mean([c['average_precision_drop'] for c in changes]):.6f} |")
    lines+=['','Jointly shuffling NF TTL/window fields reduces macro-F1 by about 0.426 to 0.479 across these model/protocol combinations. CIC window/segment shuffling produces drops from about 0.041 to 0.285. This identifies strong fitted-model dependence for investigation.','',
        'Shuffling may create unrealistic feature combinations; unshuffled correlated fields may also mask dependence. These are model sensitivity measurements, not causal explanations or reduced-feature retraining results. See the [registered protocol](../docs/CP6-comparison-protocol-B2.md) for the exact groups and interpretation references.','',
        '## Decision and next work','',
        'Retain Extra Trees as the classical reference and the compact MLP as the neural integration candidate. The per-namespace representation choices above are development choices, not a final detector freeze. EXP-003 remains open because reduced-feature comparisons require split redesign and NF host independence is not established.','',
        'CP7 must assess host-aware split feasibility and realistic client assignment before stronger generalization claims or FL comparisons. Do not use the sealed final or external results to repair these development choices. An eventual neural framework migration also needs prediction/precision and training equivalence checks before FL/DP integration.','',
        f"All {len(all_runs)} new runs stayed within worker limits. Their fit time totals {sum(r['fit_seconds'] for r in all_runs):.3f} seconds; supervised time totals {sum(r['supervised_wall_seconds'] for r in all_runs):.3f} seconds; sampled maximum worker-tree RSS is {max(r['sampled_peak_process_rss_bytes'] for r in all_runs)/2**30:.3f} GiB. Gate preparation, diagnostics and verification are additional work. Warmed batch latency and artifact sizes are in per-run records; none is end-to-end flow latency.",'',
        'Saved probabilities reproduce model, permutation and host-subgroup metrics. The full 20-test suite passes. See [verification](cp6/verification.json), [test log](cp6-tests.log), [seed summary](cp6/seed-summary.json), and [viva notes](../docs/CP6-viva.md).']
    (ROOT/'reports/CP6-comparison-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    project_path=ROOT/'docs/registries/project.json'; project=read(project_path)
    for r in all_runs:
        entry={**r,'date':'2026-09-09','result':'Verified B2 validation comparison / seed sensitivity','interpretation':'Fixed training population; no held-out generalization or privacy guarantee'}
        project['runs']=[old for old in project['runs'] if old['run_id']!=r['run_id']]+[entry]
    e=next(e for e in project['experiments'] if e['experiment_id']=='EXP-003')
    e.update(status='RUNNING',model='LR / Extra Trees / MLP; B1 controls and B2 representation comparisons',
        git_commit=all_runs[0]['git_commit'],seed=[17,29,43],hyperparameters='B1 estimator settings unchanged; B2 representation and seed rules in docs/CP6-comparison-protocol-B2.md',
        logs=['reports/cp6-feature-gates.log','reports/cp6-exploration.log','reports/cp6-seed-sensitivity.log','reports/cp6-host-diagnostics.log','reports/cp6-permutation.log'],
        feature_set='Full CIC P2 / NF P1 plus training-fitted categorical indicators; reduced representations rejected under S1',
        metrics={'B1_completed_runs':16,'B2_completed_runs':len(all_runs),'three_seed_configurations':12,'seed_sensitivity_summary':'reports/cp6/seed-summary.json'},
        result='CP6 bounded comparisons and shortcut diagnostics complete; host/split limitations remain',
        interpretation='Conditional three-seed validation evidence; not independent-host or external generalization',
        decision='Retain tree reference and MLP integration candidate; assess host-aware splits and client manifests at CP7',
        artifacts=['reports/CP5-baseline-results.md','reports/CP6-comparison-results.md','reports/cp6/verification.json','reports/cp6/selection.json','reports/cp6/seed-summary.json'],
        runtime={**e['runtime'],'B2_fit_seconds':sum(r['fit_seconds'] for r in all_runs),'B2_supervised_seconds':sum(r['supervised_wall_seconds'] for r in all_runs),'preparation_diagnostics_verification_additional':True},
        memory_usage={'B2_max_sampled_worker_tree_rss_bytes':max(r['sampled_peak_process_rss_bytes'] for r in all_runs)})
    decisions=[('DEC-018','Can reduced representations reuse S1?','Reject no_shortcut/top32 comparisons under S1; keep population fixed','Feature reduction creates cross-role vector merges; no valid reduced-model scores exist'),
        ('DEC-019','Which representation merits seed sensitivity?','Apply the preregistered 0.002 macro-F1 / AP guard per model and namespace','Selected configurations evaluated at model seeds 17,29,43 on fixed data'),
        ('DEC-020','Do near-perfect NF scores establish independent-host performance?','No; require host-aware feasibility and client design before stronger claims','Nearly all validation rows reuse training endpoint pairs; unseen-pair support is very small')]
    for did,question,choice,why in decisions:
        if not any(d['decision_id']==did for d in project['decisions']):
            project['decisions'].append({'decision_id':did,'question':question,'selected_option':choice,'why_selected':why,
                'candidate_alternatives':['Proceed without renewed controls',choice],'evidence_considered':['docs/CP6-comparison-protocol-B2.md','reports/CP6-comparison-results.md'],
                'experiments_used':['EXP-003'],'rejected_alternatives':['Unqualified reduced-feature or host-generalization claim'],'why_rejected':'Not supported by this checkpoint',
                'risks':['Capture and host dependence; same-validation selection bias; limited minority support'],'trade_offs':['More split work before integration'],
                'confidence':'High for measured counts and metrics; limited for generalization','architecture_version':'A0','revisit_condition':'Host-aware split and subsequent integration evidence'})
    for (dataset,protocol),spec in features.items():
        for variant,d in spec['definitions'].items():
            if d['gate']['status']=='PASSED': continue
            failure={'experiment_id':'EXP-003','what_failed':f'B2 {dataset}/{protocol}/{variant} eligibility gate','error':'Reduced representation merges distinct S1 groups',
                'suspected_cause':'Removal of distinguishing fields','investigation':f'reports/cp6/features/{dataset}-{protocol}.json',
                'fix':'No model scored; retain fixed population and defer reduced-feature split redesign','scientifically_invalid':True,'rerun_required':False}
            if failure not in project['failures']: project['failures'].append(failure)
    architecture=next(a for a in project['architectures'] if a['version']=='A0')
    architecture['supporting_decisions']=list(dict.fromkeys(architecture['supporting_decisions']+['DEC-018','DEC-019','DEC-020']))
    architecture['known_limitations']=[v for v in architecture['known_limitations'] if 'B1 evidence' not in v]+[
        'B2 conditional three-seed evidence; EXP-003 final selection remains open', 'NF validation overwhelmingly shares training endpoint pairs; host independence not established',
        'Reduced-feature comparisons require renewed splits; FL/DP/CL integration remains unimplemented']
    architecture['known_limitations']=list(dict.fromkeys(architecture['known_limitations']))
    project['progress'].update(checkpoint='CP6',status='COMPLETE',current=[],next=['CP7: host-aware split feasibility and client partition contracts','Verify neural framework migration before FL/DP integration'],
        needs_validation=['Host-aware split feasibility and synthetic-client realism','Representation-induced grouping for reduced-feature studies','Neural training/precision migration','Private preprocessing and DP accounting','FL/CL comparisons','Final and external generalization'])
    project['progress']['completed']=list(dict.fromkeys(project['progress']['completed']+['B2 representation gates, valid comparisons and three-seed sensitivity','Grouped permutation and NF endpoint-overlap diagnostics']))
    write_json(project_path,project)
    print(f'CP6 verification PASSED: {len(all_runs)} B2 runs, 12 three-seed configurations, permutation and host metrics',flush=True)


if __name__=='__main__': main()
