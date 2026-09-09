"""N1 local artifact and NumPy-layout preflight. No training or downloads."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import joblib
import numpy as np
import psutil
from threadpoolctl import threadpool_limits
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, bundle, load_partition
from run_cp6 import feature_spec
from cp6_features import transform
from neural_migration import numpy_predict


def binding(path):
    return {'path': str(path), 'sha256': sha(path)}


def main():
    output = ROOT/'reports/cp8/preparation.json'
    if output.exists():
        raise RuntimeError('Preserve existing preflight; refusing overwrite')
    started = time.perf_counter()
    selection_path = ROOT/'reports/cp6/selection.json'
    selection = json.loads(selection_path.read_text())
    result = {'version': 'N1', 'status': 'RUNNING', 'checkpoint_complete': False,
              'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'bindings': [binding(selection_path), binding(__file__), binding(ROOT/'scripts/neural_migration.py'),
                           binding(ROOT/'docs/CP8-neural-migration-protocol-N1.md')],
              'checks': [], 'new_model_fits': 0, 'torch_executed': False,
              'final_test_accessed': False, 'external_test_accessed': False}
    write_json(output, result)
    try:
        with threadpool_limits(limits=2):
            for dataset in DATASETS:
                for protocol in PROTOCOLS:
                    selected = next(s for s in selection['selected'] if s['dataset'] == dataset
                                    and s['protocol'] == protocol and s['model_kind'] == 'mlp')
                    reports = []
                    for item in selected['candidate_reports']:
                        assert sha(item['path']) == item['sha256']
                        reports.append((Path(item['path']), json.loads(Path(item['path']).read_text())))
                    source_path, source = next((p, r) for p, r in reports if r['run_id'] == selected['seed17_run_id'])
                    assert source['status'] == 'COMPLETED' and source['exit_code'] == 0
                    for name in ['model_artifact', 'validation_predictions']:
                        assert sha(source[name]['path']) == source[name]['sha256']
                    version, pipe, params = bundle(dataset, protocol)
                    assert source['transform_sha256'] == pipe['transform_sha256']
                    assert source['fit_group_set_sha256'] == pipe['fit_group_set_sha256']
                    spec, spec_path = feature_spec(dataset, protocol)
                    definition = spec['definitions'][selected['representation']]
                    assert definition['gate']['status'] == 'PASSED'
                    artifact = joblib.load(source['model_artifact']['path'])
                    if isinstance(artifact, dict):
                        assert artifact['definition'] == definition
                        assert artifact['base_transform_sha256'] == pipe['transform_sha256']
                        model = artifact['model']
                    else:
                        assert selected['representation'] == 'full'
                        model = artifact
                    x, y, _ = load_partition(dataset, protocol, 'validation', pipe, len(params['output_names']))
                    z = transform(x, definition)
                    p = numpy_predict(model, z)
                    reference = np.load(source['validation_predictions']['path'], allow_pickle=False)
                    assert p.shape == reference.shape == y.shape
                    assert np.isfinite(p).all() and np.isfinite(reference).all()
                    delta = float(np.max(np.abs(p-reference)))
                    disagreements = int(np.sum((p >= .5) != (reference >= .5)))
                    check = {'dataset': dataset, 'protocol': protocol, 'representation': selected['representation'],
                             'preprocessing_version': version, 'rows': len(y), 'width': z.shape[1],
                             'max_abs_delta': delta, 'decision_disagreements_05': disagreements,
                             'status': 'PASSED' if delta <= 1e-12 else 'FAILED',
                             'bindings': [binding(source_path), binding(spec_path), source['model_artifact'],
                                          source['validation_predictions'], binding(pipe['transform_path'])]}
                    result['checks'].append(check)
                    write_json(output, result)
                    print(f'{dataset}/{protocol}: {check["status"]}; {len(y)} rows; max delta {delta:.3g}', flush=True)
                    assert check['status'] == 'PASSED'
                    del x, z, y, p, reference, model, artifact
        result['status'] = 'PREPARATION_PASSED_RUNTIME_PENDING'
    except Exception as exc:
        result.update(status='FAILED', error=repr(exc))
        raise
    finally:
        result['elapsed_seconds'] = time.perf_counter()-started
        write_json(output, result)


def supervise():
    output = ROOT/'reports/cp8/preparation.json'
    if output.exists():
        raise RuntimeError('Preserve existing preflight; refusing overwrite')
    log = ROOT/'reports/cp8/preparation.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter(); peak = 0; stopped = None
    env = dict(os.environ, OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    with log.open('w', encoding='utf-8') as handle:
        proc = subprocess.Popen([sys.executable, '-u', __file__, '--worker'], cwd=ROOT, env=env,
                                stdout=handle, stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        observed = psutil.Process(proc.pid)
        while proc.poll() is None:
            tree = [observed]
            try:
                tree += observed.children(recursive=True)
                rss = 0
                for member in tree:
                    try: rss += member.memory_info().rss
                    except psutil.NoSuchProcess: pass
                peak = max(peak, rss)
            except psutil.NoSuchProcess: pass
            if peak > 12*2**30 or time.perf_counter()-started > 600:
                stopped = 'Worker-tree RSS or wall-time cap exceeded'
                for member in reversed(tree):
                    try: member.kill()
                    except psutil.NoSuchProcess: pass
                break
            time.sleep(.5)
        code = proc.wait()
    result = json.loads(output.read_text()) if output.exists() else {'status': 'FAILED'}
    result.update(exit_code=code, sampled_peak_process_rss_bytes=peak,
                  supervised_wall_seconds=time.perf_counter()-started,
                  rss_scope='Worker and descendants, sampled every 0.5 seconds', resource_limit_stop=stopped)
    if code != 0 or stopped:
        result['status'] = 'FAILED'
    write_json(output, result)
    print(log.read_text(encoding='utf-8'), end='')
    if result['status'] != 'PREPARATION_PASSED_RUNTIME_PENDING':
        raise RuntimeError('Preflight failed; preserve artifacts and inspect log')


if __name__ == '__main__':
    if sys.argv[1:] == ['--worker']:
        main()
    elif not sys.argv[1:]:
        supervise()
    else:
        raise SystemExit('Usage: prepare_cp8.py [--worker]')
