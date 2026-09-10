"""Re-read bound artifacts, reproduce predictions/metrics and apply frozen N1 rules."""
import json
import time
from pathlib import Path
import numpy as np
import torch
from sklearn.metrics import f1_score
from threadpoolctl import threadpool_limits
from audit_datasets import write_json
from preprocess_p1 import sha
from baseline_metrics import evaluate, threshold_for_fpr
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, load_partition
from run_cp8 import context, ident, CANDIDATES, SEEDS
from neural_runtime import configure, network, predict
from cp6_features import transform


def read(path): return json.loads(Path(path).read_text())
def bind(path): return {'path': str(path), 'sha256': sha(path)}


def verify_bindings(r):
    assert r['status'] == 'COMPLETED' and r['exit_code'] == 0 and r['resource_limit_stop'] is None
    assert not r['final_test_accessed'] and not r['external_test_accessed']
    assert r['script_sha256'] == sha(ROOT/'scripts/run_cp8.py')
    assert r['runtime_script_sha256'] == sha(ROOT/'scripts/neural_runtime.py')
    for b in r['source_bindings']+r['bindings']:
        assert sha(b['path']) == b['sha256'], b['path']
    assert r['sampled_peak_process_rss_bytes'] <= 12*2**30
    assert r['cuda_peak_reserved_bytes'] <= 4*2**30
    assert r['supervised_wall_seconds'] <= 601  # Half-second monitoring granularity.


def main():
    out = ROOT/'reports/cp8/verification.json'; selection_path = ROOT/'reports/cp8/selection.json'
    if out.exists() or selection_path.exists(): raise RuntimeError('Refusing overwrite of verification/selection')
    start = time.perf_counter(); configure()
    tests = (ROOT/'reports/cp8/runtime-tests.log').read_text(encoding='utf-8')
    assert 'Ran 32 tests' in tests and tests.strip().endswith('OK')
    report = {'status': 'RUNNING', 'script_sha256': sha(__file__), 'tests_passed': 32,
        'report_bindings': [], 'migration_checks': [], 'training_checks': [], 'final_test_accessed': False}
    selection = {'version': 'N1', 'status': 'FROZEN', 'rule': 'N1: SD<=.01; mean macro-F1/AP loss<=.002 vs B2; rank F1/AP/lower LR',
        'historical_baseline': bind(ROOT/'reports/cp6/seed-summary.json'), 'scopes': []}
    baseline = read(ROOT/'reports/cp6/seed-summary.json')['summaries']
    with threadpool_limits(limits=2):
        for dataset in DATASETS:
            for protocol in PROTOCOLS:
                _, pipe, params, definition, source, _ = context(dataset, protocol)
                xv, yv, lv = load_partition(dataset, protocol, 'validation', pipe, len(params['output_names']))
                xv = transform(xv, definition)
                universe = sorted(set(read(ROOT/'reports/splits/contracts'/f'{dataset}.json')['raw_to_canonical_label'].values()))
                mig_path = ROOT/'reports/cp8/runs'/f'{ident("migration",dataset,protocol)}.json'
                mig = read(mig_path); verify_bindings(mig); report['report_bindings'].append(bind(mig_path))
                ref = np.load(source['validation_predictions']['path'], allow_pickle=False)
                assert sha(mig['migrated_model']['path']) == mig['migrated_model']['sha256']
                state = torch.load(mig['migrated_model']['path'], map_location='cpu', weights_only=True)
                errors = {}
                for device, dtype, name in [('cpu',torch.float64,'cpu'),('cuda',torch.float32,'cuda')]:
                    model = network(xv.shape[1], dtype=dtype, device=device); model.load_state_dict(state)
                    p = predict(model, xv); b = mig[name+'_predictions']; assert sha(b['path']) == b['sha256']
                    assert np.array_equal(p, np.load(b['path'], allow_pickle=False))
                    errors[name] = float(np.max(np.abs(p-ref)))
                    assert errors[name] == mig[name+'_max_abs_delta']
                assert errors['cpu'] <= 1e-12 and errors['cuda'] <= 1e-4
                assert int(np.sum((p >= .5) != (ref >= .5))) == mig['cuda_decision_disagreements']
                assert mig['cuda_disagreement_rate'] <= 1e-4 and mig['roundtrip_max_abs_delta'] <= 1e-12
                report['migration_checks'].append({'dataset': dataset, 'protocol': protocol, 'status': 'PASSED', 'errors': errors})
                xv = xv.astype(np.float32); historical = next(b for b in baseline if b['dataset'] == dataset
                    and b['protocol'] == protocol and b['model_kind'] == 'mlp')
                summaries = []; initial = {}
                for candidate in CANDIDATES:
                    runs = []
                    for seed in SEEDS:
                        path = ROOT/'reports/cp8/runs'/f'{ident("train",dataset,protocol,candidate,seed)}.json'
                        r = read(path); verify_bindings(r); report['report_bindings'].append(bind(path))
                        for key in ['initial_weights','model_artifact','validation_predictions','migration_gate','optimizer_tests']:
                            assert sha(r[key]['path']) == r[key]['sha256']
                        assert r['train_rows'] == 100000 and r['validation_rows'] == len(yv)
                        assert r['input_artifacts'] == pipe['artifacts'] and r['fit_group_set_sha256'] == pipe['fit_group_set_sha256']
                        assert len(r['loss_curve']) == 20 and np.isfinite(r['loss_curve']).all()
                        assert r['hyperparameters']['lr'] == CANDIDATES[candidate] and r['hyperparameters']['epochs'] == 20
                        saved = torch.load(r['model_artifact']['path'], weights_only=True, map_location='cpu')
                        assert saved['definition'] == definition and saved['transform_sha256'] == pipe['transform_sha256']
                        model = network(xv.shape[1], device='cuda'); model.load_state_dict(saved['state_dict'])
                        p = np.load(r['validation_predictions']['path'], allow_pickle=False)
                        recomputed = predict(model, xv); assert np.array_equal(p, recomputed)
                        assert evaluate(yv,p,lv,universe) == r['metrics_05']
                        assert evaluate(yv,p,lv,universe,threshold_for_fpr(yv,p)) == r['metrics_fpr01']
                        # Separate library macro-F1 and direct confusion support checks.
                        assert abs(float(f1_score(yv,p>=.5,average='macro',labels=[0,1]))-r['metrics_05']['binary_macro_f1']) < 1e-12
                        assert sum(r['metrics_05']['confusion'].values()) == len(yv)
                        assert r['metrics_fpr01']['confusion']['fp'] <= int(.01*int((yv == 0).sum()))
                        saved_init = torch.load(r['initial_weights']['path'], weights_only=True, map_location='cpu')
                        expected_init = network(xv.shape[1], seed=seed).state_dict()
                        assert all(torch.equal(saved_init[k], expected_init[k]) for k in expected_init)
                        if seed in initial: assert all(torch.equal(saved_init[k],initial[seed][k]) for k in saved_init)
                        initial[seed] = saved_init
                        runs.append(r)
                        report['training_checks'].append({'run_id': r['run_id'], 'status': 'PASSED',
                            'full_prediction_reproduction': True, 'metrics_reproduced': True, 'registered_initialization_verified': True})
                    f1 = [r['metrics_05']['binary_macro_f1'] for r in runs]; ap = [r['metrics_05']['average_precision'] for r in runs]
                    summary = {'candidate': candidate, 'learning_rate': CANDIDATES[candidate],
                        'run_ids': [r['run_id'] for r in runs], 'macro_f1_by_seed': dict(zip(map(str,SEEDS),f1)),
                        'macro_f1_mean': float(np.mean(f1)), 'macro_f1_sample_sd': float(np.std(f1,ddof=1)),
                        'average_precision_mean': float(np.mean(ap)), 'fit_seconds_total': sum(r['fit_seconds'] for r in runs)}
                    summary['eligible'] = (summary['macro_f1_sample_sd'] <= .01 and
                        summary['macro_f1_mean'] >= historical['macro_f1_mean']-.002 and
                        summary['average_precision_mean'] >= historical['average_precision_mean']-.002)
                    summaries.append(summary)
                eligible = [s for s in summaries if s['eligible']]
                winner = min(eligible, key=lambda s:(-s['macro_f1_mean'],-s['average_precision_mean'],s['learning_rate'])) if eligible else None
                selection['scopes'].append({'dataset': dataset, 'protocol': protocol, 'representation': historical['representation'],
                    'historical_b2_mlp_macro_f1_mean': historical['macro_f1_mean'],
                    'historical_b2_mlp_macro_f1_sample_sd': historical['macro_f1_sample_sd'],
                    'historical_b2_mlp_ap_mean': historical['average_precision_mean'], 'candidates': summaries,
                    'selected_candidate': winner['candidate'] if winner else None,
                    'status': 'PILOT_ELIGIBLE' if winner else 'STABILITY_OR_QUALITY_UNRESOLVED'})
                print(f'{dataset}/{protocol}: verified 1 migration + 6 training runs; {selection["scopes"][-1]["status"]}', flush=True)
    assert len(report['training_checks']) == 24 and len(report['migration_checks']) == 4
    write_json(selection_path, selection)
    report.update(status='PASSED', selection=bind(selection_path), elapsed_seconds=time.perf_counter()-start)
    write_json(out, report)


if __name__ == '__main__': main()
