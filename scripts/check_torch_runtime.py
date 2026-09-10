"""Installed-runtime smoke check only; no project data or model training."""
import json
import os
import platform
import subprocess
import sys
import time
from importlib.metadata import distributions
from pathlib import Path

os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'

import numpy as np
import torch
from audit_datasets import write_json
from preprocess_p1 import sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT/'reports/cp8/runtime-installation.json'
    if path.exists():
        raise RuntimeError('Preserve existing runtime report; refusing overwrite')
    start = time.perf_counter()
    report = {
        'status': 'RUNNING', 'scope': 'Package installation and synthetic arithmetic smoke check only',
        'script_sha256': sha(__file__), 'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'torch': str(torch.__version__), 'numpy': np.__version__,
        'wheel_cuda_version': torch.version.cuda, 'cuda_available': torch.cuda.is_available(),
        'package_index': 'https://download.pytorch.org/whl/cu128', 'requested_package': 'torch==2.10.0',
        'authorization': 'User explicitly requested download and installation, then approval before project continuation',
        'dataset_accessed': False, 'project_model_trained': False, 'migration_gate_executed': False,
        'checkpoint_complete': False, 'checks': [],
        'packages': sorted([{'name': d.metadata['Name'], 'version': d.version} for d in distributions()], key=lambda d: d['name'].lower())
    }
    write_json(path, report)
    try:
        assert str(torch.__version__) == '2.10.0+cu128', 'Unexpected Torch build'
        assert torch.version.cuda == '12.8' and torch.cuda.is_available(), 'CUDA runtime unavailable'
        torch.set_num_threads(2)
        torch.set_num_interop_threads(2)
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        props = torch.cuda.get_device_properties(0)
        torch.cuda.set_per_process_memory_fraction(min(1.0, 4*2**30/props.total_memory), 0)
        torch.cuda.reset_peak_memory_stats(0)
        report.update(device_name=props.name, device_total_memory_bytes=props.total_memory,
                      compute_capability=list(torch.cuda.get_device_capability(0)),
                      gpu_driver_query=subprocess.check_output(
                          ['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'], text=True).strip(),
                      torch_cpu_threads=torch.get_num_threads(), deterministic_algorithms=True,
                      tf32_enabled=False, cuda_allocator_limit_bytes=4*2**30)
        x = np.array([[1., 2.], [-3., 4.], [5., -6.]])
        w = np.array([[2., -1.], [3., 4.]])
        expected = x @ w
        expected_grad = 2*x.T @ expected
        for device, dtype in [('cpu', torch.float64), ('cuda', torch.float32)]:
            xt = torch.tensor(x, dtype=dtype, device=device)
            wt = torch.tensor(w, dtype=dtype, device=device, requires_grad=True)
            out = xt @ wt
            out.square().sum().backward()
            if device == 'cuda': torch.cuda.synchronize()
            forward_delta = float(np.max(np.abs(out.detach().cpu().numpy()-expected)))
            gradient_delta = float(np.max(np.abs(wt.grad.detach().cpu().numpy()-expected_grad)))
            assert forward_delta == 0 and gradient_delta == 0
            report['checks'].append({'device': device, 'dtype': str(dtype), 'forward_max_abs_error': forward_delta,
                                     'gradient_max_abs_error': gradient_delta, 'status': 'PASSED'})
        report.update(status='INSTALLED_SMOKE_CHECK_PASSED',
                      cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(0),
                      cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(0))
    except Exception as exc:
        report.update(status='FAILED', error=repr(exc))
        raise
    finally:
        report['elapsed_seconds'] = time.perf_counter()-start
        write_json(path, report)
    print(json.dumps({k: report[k] for k in ['status', 'torch', 'wheel_cuda_version', 'device_name', 'checks']}, indent=2))


if __name__ == '__main__': main()
