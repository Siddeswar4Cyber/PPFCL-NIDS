"""N1 sequential migration and bounded native-Adam stability workers."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import joblib
import numpy as np
import psutil
import torch
from threadpoolctl import threadpool_limits
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, bundle, load_partition
from run_cp6 import feature_spec
from cp6_features import transform
from baseline_metrics import evaluate, threshold_for_fpr
from neural_migration import to_torch
from neural_runtime import configure, network, objective, optimizer, predict

CANDIDATES = {'lr001': .001, 'lr0003': .0003}
SEEDS = [17, 29, 43]


def read(path): return json.loads(Path(path).read_text())
def binding(path): return {'path': str(path), 'sha256': sha(path)}
def ident(stage, dataset, protocol, candidate='none', seed=17):
    return f'N1-{stage}-{dataset}-{protocol}-{candidate}-s{seed}'


def context(dataset, protocol):
    selection_path = ROOT/'reports/cp6/selection.json'
    selected = next(s for s in read(selection_path)['selected'] if s['dataset'] == dataset
                    and s['protocol'] == protocol and s['model_kind'] == 'mlp')
    candidates = []
    for b in selected['candidate_reports']:
        assert sha(b['path']) == b['sha256']
        candidates.append((Path(b['path']), read(b['path'])))
    source_path, source = next((p, r) for p, r in candidates if r['run_id'] == selected['seed17_run_id'])
    assert source['status'] == 'COMPLETED' and source['exit_code'] == 0
    for name in ['model_artifact', 'validation_predictions']:
        assert sha(source[name]['path']) == source[name]['sha256']
    version, pipe, params = bundle(dataset, protocol)
    spec, spec_path = feature_spec(dataset, protocol)
    definition = spec['definitions'][selected['representation']]
    assert definition['gate']['status'] == 'PASSED'
    assert source['transform_sha256'] == pipe['transform_sha256']
    assert source['fit_group_set_sha256'] == pipe['fit_group_set_sha256']
    return version, pipe, params, definition, source, {
        'representation': selected['representation'],
        'bindings': [binding(selection_path), binding(source_path), binding(spec_path),
                     binding(pipe['transform_path']), source['model_artifact'], source['validation_predictions']]}


def migration(dataset, protocol, result, folder):
    version, pipe, params, definition, source, meta = context(dataset, protocol)
    result.update(meta, preprocessing_version=version, transform_sha256=pipe['transform_sha256'])
    x, y, _ = load_partition(dataset, protocol, 'validation', pipe, len(params['output_names']))
    z = transform(x, definition); del x
    saved = joblib.load(source['model_artifact']['path'])
    if isinstance(saved, dict):
        assert saved['definition'] == definition and saved['base_transform_sha256'] == pipe['transform_sha256']
        model = saved['model']
    else:
        assert meta['representation'] == 'full'; model = saved
    reference = np.load(source['validation_predictions']['path'], allow_pickle=False)
    assert reference.shape == y.shape
    cpu = to_torch(model); p64 = predict(cpu, z)
    cpu_delta = float(np.max(np.abs(p64-reference)))
    cpu_path = folder/'migrated-cpu.pt'
    torch.save(cpu.state_dict(), cpu_path)
    restored = network(z.shape[1], dtype=torch.float64)
    restored.load_state_dict(torch.load(cpu_path, weights_only=True, map_location='cpu'))
    reloaded = predict(restored, z)
    roundtrip_delta = float(np.max(np.abs(reloaded-p64)))
    gpu = to_torch(model, device='cuda', dtype=torch.float32)
    p32 = predict(gpu, z)
    gpu_delta = float(np.max(np.abs(p32-reference)))
    changed = (p32 >= .5) != (reference >= .5)
    rate = float(changed.mean())
    result.update(rows=len(y), input_features=z.shape[1], cpu_max_abs_delta=cpu_delta,
        cpu_decision_disagreements=int(np.sum((p64 >= .5) != (reference >= .5))),
        roundtrip_max_abs_delta=roundtrip_delta, cuda_max_abs_delta=gpu_delta,
        cuda_decision_disagreements=int(changed.sum()), cuda_disagreement_rate=rate,
        changed_reference_distances_to_threshold=np.abs(reference[changed]-.5).tolist(),
        changed_cuda_distances_to_threshold=np.abs(p32[changed]-.5).tolist(),
        migrated_model=binding(cpu_path), gates={'cpu': cpu_delta <= 1e-12, 'roundtrip': roundtrip_delta <= 1e-12,
        'cuda_probability': gpu_delta <= 1e-4, 'cuda_decisions': rate <= 1e-4})
    for name, p in [('cpu', p64), ('cuda', p32)]:
        path = folder/f'{name}-validation-probabilities.npy'; np.save(path, p, allow_pickle=False)
        result[name+'_predictions'] = binding(path)
    if not all(result['gates'].values()): raise RuntimeError('N1 migration tolerance failed; no automatic relaxation')


def train(dataset, protocol, candidate, seed, result, folder):
    gate_path = ROOT/'reports/cp8/runs'/f'{ident("migration", dataset, protocol)}.json'
    gate = read(gate_path)
    assert gate['status'] == 'COMPLETED' and gate['exit_code'] == 0 and all(gate['gates'].values())
    assert gate['script_sha256'] == sha(__file__) and gate['runtime_script_sha256'] == sha(ROOT/'scripts/neural_runtime.py')
    tests_path = ROOT/'reports/cp8/optimizer-tests.log'
    tests = tests_path.read_text(encoding='utf-8')
    assert 'Ran 3 tests' in tests and tests.strip().endswith('OK')
    version, pipe, params, definition, _, meta = context(dataset, protocol)
    result.update(meta, migration_gate=binding(gate_path), optimizer_tests=binding(tests_path),
        preprocessing_version=version, transform_sha256=pipe['transform_sha256'],
        fit_group_set_sha256=pipe['fit_group_set_sha256'], input_artifacts=pipe['artifacts'])
    width = len(params['output_names'])
    x, y, _ = load_partition(dataset, protocol, 'train', pipe, width)
    xv, yv, lv = load_partition(dataset, protocol, 'validation', pipe, width)
    x = transform(x, definition).astype(np.float32); xv = transform(xv, definition).astype(np.float32)
    assert len(y) == 100000
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    model = network(x.shape[1], device='cuda', seed=seed)
    opt = optimizer(model, CANDIDATES[candidate]); rng = np.random.default_rng(seed)
    xt = torch.as_tensor(x, device='cuda'); yt = torch.as_tensor(y.astype(np.float32), device='cuda')
    init_path = folder/'initial-weights.pt'; torch.save({k: v.cpu() for k,v in model.state_dict().items()}, init_path)
    result.update(train_rows=len(y), validation_rows=len(yv), input_features=x.shape[1], input_dtype='float32',
        initial_weights=binding(init_path), hyperparameters={'lr': CANDIDATES[candidate], 'epochs': 20, 'batch_size': 256,
        'hidden_sizes': [64,32], 'alpha_weight_only_per_actual_batch': .0001, 'betas': [.9,.999], 'eps': 1e-8,
        'weight_decay': 0, 'foreach': False, 'fused': False, 'early_stopping': False}, loss_curve=[])
    torch.cuda.synchronize(); started = time.perf_counter()
    for epoch in range(20):
        model.train(); order = torch.as_tensor(rng.permutation(len(y)), device='cuda')
        total_loss = torch.zeros((), device='cuda', dtype=torch.float64)
        for start in range(0, len(y), 256):
            ids = order[start:start+256]; opt.zero_grad(set_to_none=True)
            loss = objective(model, xt[ids], yt[ids]); loss.backward(); opt.step()
            total_loss += loss.detach().double()*len(ids)
        average = float((total_loss/len(y)).item())
        if not np.isfinite(average) or not all(torch.isfinite(p).all().item() for p in model.parameters()):
            raise RuntimeError('Nonfinite training loss or parameters')
        result['loss_curve'].append(average)
        print(f'epoch {epoch+1}/20; training objective {average:.8g}', flush=True)
    torch.cuda.synchronize(); result['fit_seconds'] = time.perf_counter()-started
    tick = time.perf_counter(); p = predict(model, xv)
    result['validation_prediction_seconds'] = time.perf_counter()-tick
    universe = sorted(set(read(ROOT/'reports/splits/contracts'/f'{dataset}.json')['raw_to_canonical_label'].values()))
    result['metrics_05'] = evaluate(yv, p, lv, universe)
    result['metrics_fpr01'] = evaluate(yv, p, lv, universe, threshold_for_fpr(yv, p))
    assert result['metrics_fpr01']['confusion']['fp'] <= int(.01*int((yv == 0).sum()))
    model_path = folder/'model.pt'; pred_path = folder/'validation-probabilities.npy'
    torch.save({'state_dict': {k:v.cpu() for k,v in model.state_dict().items()}, 'definition': definition,
                'transform_sha256': pipe['transform_sha256'], 'input_features': x.shape[1]}, model_path)
    np.save(pred_path, p, allow_pickle=False)
    restored = network(x.shape[1], device='cuda')
    restored.load_state_dict(torch.load(model_path, weights_only=True, map_location='cpu')['state_dict'])
    roundtrip = float(np.max(np.abs(predict(restored, xv[:4096])-p[:4096])))
    assert roundtrip == 0
    result.update(model_artifact=binding(model_path), validation_predictions=binding(pred_path),
        model_roundtrip_max_abs_delta=roundtrip, parameter_count=sum(v.numel() for v in model.parameters()))


def worker(stage, dataset, protocol, candidate, seed):
    run_id = ident(stage, dataset, protocol, candidate, seed)
    output = ROOT/'reports/cp8/runs'/f'{run_id}.json'; folder = ROOT/'models/N1'/run_id
    if output.exists() or folder.exists(): raise RuntimeError('Refusing overwrite: '+run_id)
    folder.mkdir(parents=True); started = time.perf_counter()
    result = {'run_id': run_id, 'version': 'N1', 'experiment_id': 'EXP-003', 'architecture_version': 'A0',
        'stage': stage, 'dataset': dataset, 'protocol': protocol, 'candidate': candidate, 'seed': seed, 'status': 'RUNNING',
        'git_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        'script_sha256': sha(__file__), 'runtime_script_sha256': sha(ROOT/'scripts/neural_runtime.py'),
        'source_bindings': [binding(ROOT/p) for p in ['scripts/neural_migration.py', 'scripts/baseline_metrics.py',
            'scripts/cp6_features.py','scripts/run_baseline_pilot.py','tests/test_neural_runtime.py',
            'docs/CP8-neural-migration-protocol-N1.md','reports/cp8/runtime-installation.json','requirements-neural-lock.txt']],
        'environment': {'torch': str(torch.__version__), 'numpy': np.__version__, 'python': sys.version.split()[0]},
        'client_configuration': 'Centralized development; C1 unused and unchanged', 'privacy_configuration': 'Non-private',
        'cl_configuration': 'No CL', 'final_test_accessed': False, 'external_test_accessed': False}
    write_json(output, result)
    try:
        configure()
        with threadpool_limits(limits=2):
            if stage == 'migration': migration(dataset, protocol, result, folder)
            else: train(dataset, protocol, candidate, seed, result, folder)
        result['status'] = 'COMPLETED'
    except Exception as exc:
        result.update(status='FAILED', error=repr(exc)); raise
    finally:
        result.update(worker_seconds=time.perf_counter()-started,
            cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(0),
            cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(0))
        write_json(output, result)


def supervise(stage, dataset, protocol, candidate='none', seed=17):
    run_id = ident(stage, dataset, protocol, candidate, seed)
    output = ROOT/'reports/cp8/runs'/f'{run_id}.json'
    if output.exists():
        r = read(output)
        assert r['status'] == 'COMPLETED' and r.get('exit_code') == 0 and r['script_sha256'] == sha(__file__)
        for b in r['source_bindings']: assert sha(b['path']) == b['sha256']
        print(run_id+': verified existing completion', flush=True); return
    log = ROOT/'reports/cp8/logs'/f'{run_id}.log'; log.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter(); peak = 0; stopped = None
    env = dict(os.environ, OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', CUBLAS_WORKSPACE_CONFIG=':4096:8')
    print(run_id+': START', flush=True)
    with log.open('w', encoding='utf-8') as handle:
        proc = subprocess.Popen([sys.executable, '-u', __file__, 'worker', '--stage', stage, '--dataset', dataset,
            '--protocol', protocol, '--candidate', candidate, '--seed', str(seed)], cwd=ROOT, env=env,
            stdout=handle, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        observed = psutil.Process(proc.pid)
        while proc.poll() is None:
            tree = [observed]
            try:
                tree += observed.children(recursive=True); rss = 0
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
    r = read(output) if output.exists() else {'run_id': run_id, 'status': 'FAILED'}
    r.update(exit_code=code, sampled_peak_process_rss_bytes=peak, supervised_wall_seconds=time.perf_counter()-started,
        rss_scope='Worker and descendants sampled every 0.5 seconds', resource_limit_stop=stopped, log=str(log))
    if code != 0 or stopped: r['status'] = 'FAILED'
    write_json(output, r); print(run_id+': '+r['status'], flush=True)
    if r['status'] != 'COMPLETED': raise RuntimeError('Preserve failed run and investigate: '+run_id)


def main():
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['migration','train','worker'])
    p.add_argument('--stage', choices=['migration','train']); p.add_argument('--dataset', choices=DATASETS)
    p.add_argument('--protocol', choices=PROTOCOLS); p.add_argument('--candidate', choices=['none',*CANDIDATES], default='none')
    p.add_argument('--seed', type=int, choices=SEEDS, default=17); a = p.parse_args()
    if a.action == 'worker':
        if not a.stage or not a.dataset or not a.protocol: p.error('Worker requires stage/dataset/protocol')
        if a.stage == 'train' and a.candidate == 'none': p.error('Training requires a candidate')
        worker(a.stage, a.dataset, a.protocol, a.candidate, a.seed); return
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            if a.action == 'migration': supervise('migration', dataset, protocol)
            else:
                for candidate in CANDIDATES:
                    for seed in SEEDS: supervise('train', dataset, protocol, candidate, seed)


if __name__ == '__main__': main()
