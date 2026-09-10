"""Save approved runtime setup; later CP8 execution is recorded separately."""
import json
from pathlib import Path
from audit_datasets import write_json
from preprocess_p1 import sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT/'reports/cp8/runtime-installation.json'
    r = json.loads(path.read_text())
    assert r['status'] == 'INSTALLED_SMOKE_CHECK_PASSED'
    assert r['script_sha256'] == sha(ROOT/'scripts/check_torch_runtime.py')
    assert len(r['checks']) == 2 and all(c['status'] == 'PASSED' for c in r['checks'])
    assert not r['dataset_accessed'] and not r['project_model_trained'] and not r['migration_gate_executed']
    # Keep the original baseline pins intact and explicitly check for dependency drift.
    installed = {p['name'].lower(): p['version'] for p in r['packages']}
    for line in (ROOT/'requirements-baseline.txt').read_text().splitlines():
        name, version = line.split('==')
        assert installed[name.lower()] == version, f'Baseline dependency changed: {name}'
    lock = ROOT/'requirements-neural-lock.txt'
    lock.write_text('\n'.join(p['name']+'=='+p['version'] for p in r['packages'])+'\n', encoding='utf-8')
    (ROOT/'requirements-torch.txt').write_text('--index-url https://download.pytorch.org/whl/cu128\ntorch==2.10.0+cu128\n', encoding='utf-8')
    report = ROOT/'reports/CP8-runtime-setup.md'
    report.write_text(f'''# CP8 runtime installed; migration checks next

2026-09-10. The user explicitly approved the package download and subsequently sent continue, authorizing CP8 continuation. PyTorch {r['torch']} and its required dependencies are installed in the project virtual environment. The previously rejected installation is resolved. The project is saved at this setup checkpoint; CP8 remains incomplete.

- Python: {r['python'].split()[0]}.
- PyTorch wheel CUDA runtime: {r['wheel_cuda_version']}.
- GPU: {r['device_name']}; {r['device_total_memory_bytes']/2**30:.3f} GiB reported device memory.
- Driver query: {r['gpu_driver_query']}.
- CPU float64 and CUDA float32 matrix multiplication and autograd checks both pass with zero error against a fixed NumPy arithmetic fixture.
- The original ten baseline dependency versions are unchanged.

The smoke check uses deterministic algorithms, disables TF32, limits CPU threads to two and caps the CUDA allocator at 4 GiB. Peak allocated/reserved GPU memory for this tiny fixture was {r['cuda_peak_allocated_bytes']:,} / {r['cuda_peak_reserved_bytes']:,} bytes. These measurements describe setup verification only; they do not estimate project training resources. No dataset was opened and no project model was trained.

The package inventory is saved in [requirements-neural-lock.txt](../requirements-neural-lock.txt). The CUDA-specific install specification is [requirements-torch.txt](../requirements-torch.txt); use the official CUDA index for the Torch build rather than assuming it is on the default package index. The full inventory records versions, not wheel-content hashes or a portable cross-platform environment.

The earlier [preparation report](CP8-preparation-status.md) is historical and retains the original blocked state. Current machine-readable setup evidence is [runtime-installation.json](cp8/runtime-installation.json). The NumPy artifact checks remain valid; successful installation does not establish saved-model Torch migration or optimizer correctness.

Next, under the user's continuation instruction: execute the preregistered N1 CPU/CUDA migration and serialization checks, implement and verify native-Adam gradient/update checks, then run the bounded 24-fit stability comparison. Save decisions before advancing to CP9 central/local/federated pilots. No new scope or candidate budget is authorized by this setup check.
''', encoding='utf-8')
    p = ROOT/'docs/registries/project.json'; project = json.loads(p.read_text())
    project['runtime_installation'] = {'status': r['status'], 'path': str(path), 'sha256': sha(path),
                                       'lock_path': str(lock), 'lock_sha256': sha(lock),
                                       'baseline_dependency_drift': False, 'project_continuation': 'AUTHORIZED_BY_USER_CONTINUE'}
    project['progress'].update(status='IN_PROGRESS',
        current=['N1 preparation and approved PyTorch CUDA installation complete; continuation authorized'],
        next=['Execute N1 migration/optimizer gates and registered stability comparison',
              'Preregister comparable central/local/FL pilots on C1'], blocked=[])
    item = 'PyTorch 2.10.0+cu128 installed; CPU/GPU arithmetic and autograd smoke checks pass'
    if item not in project['progress']['completed']: project['progress']['completed'].append(item)
    write_json(p, project)
    for filename, replacement in [
        ('README.md', 'Current checkpoint: CP8 IN PROGRESS. PyTorch 2.10.0+cu128 is installed and CPU/GPU smoke checks pass on the RTX 4050. Setup is saved; the user authorized continuation. The four prior NumPy reconstruction checks and 29 tests passed; Torch model migration, optimizer checks and 24 planned stability fits remain outstanding. See [runtime setup](reports/CP8-runtime-setup.md), [N1 protocol](docs/CP8-neural-migration-protocol-N1.md), and [project status](docs/STATUS.md).'),
        ('docs/STATUS.md', 'Current checkpoint: CP8 IN PROGRESS; continuation authorized. The approved PyTorch 2.10.0+cu128 installation and CPU/GPU arithmetic/autograd smoke checks pass on the RTX 4050. The previous download block is resolved. N1 preparation and the prior 29 tests remain passed; Torch model migration, optimizer checks and 24 planned fits remain outstanding. CP0 through CP7 remain complete. See [runtime setup](../reports/CP8-runtime-setup.md).')]:
        p = ROOT/filename; text = p.read_text(encoding='utf-8'); paragraphs = text.split('\n\n')
        indices = [i for i, paragraph in enumerate(paragraphs) if paragraph.startswith('Current checkpoint:')]
        assert len(indices) == 1
        paragraphs[indices[0]] = replacement
        p.write_text('\n\n'.join(paragraphs), encoding='utf-8')
    print('Runtime setup saved; continuation authorized')


if __name__ == '__main__': main()
