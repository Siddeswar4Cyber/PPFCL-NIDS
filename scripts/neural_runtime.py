"""N1 runtime, fixed initialization and explicit native-Adam training objective."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import numpy as np
import torch


def configure():
    if str(torch.__version__) != '2.10.0+cu128' or not torch.cuda.is_available():
        raise RuntimeError('N1 requires the verified Torch 2.10.0 CUDA 12.8 runtime')
    torch.set_num_threads(2)
    torch.set_num_interop_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(min(1., 4*2**30/total), 0)
    torch.cuda.reset_peak_memory_stats(0)


def network(width, dtype=torch.float32, device='cpu', seed=17):
    model = torch.nn.Sequential(torch.nn.Linear(width, 64), torch.nn.ReLU(),
                                torch.nn.Linear(64, 32), torch.nn.ReLU(), torch.nn.Linear(32, 1))
    model = model.to(dtype=dtype, device=device)
    rng = np.random.RandomState(seed)
    with torch.no_grad():
        for layer in (model[0], model[2], model[4]):
            bound = np.sqrt(6/(layer.in_features+layer.out_features))
            w = rng.uniform(-bound, bound, (layer.in_features, layer.out_features))
            b = rng.uniform(-bound, bound, layer.out_features)
            layer.weight.copy_(torch.as_tensor(w.T, dtype=dtype, device=device))
            layer.bias.copy_(torch.as_tensor(b, dtype=dtype, device=device))
    return model


def objective(model, x, y, alpha=.0001):
    logits = model(x).squeeze(1)
    data = torch.nn.functional.binary_cross_entropy_with_logits(logits, y, reduction='mean')
    penalty = sum(layer.weight.square().sum() for layer in (model[0], model[2], model[4]))
    return data+(.5*alpha/len(y))*penalty


def optimizer(model, lr):
    return torch.optim.Adam(model.parameters(), lr=lr, betas=(.9, .999), eps=1e-8,
                            weight_decay=0, foreach=False, fused=False)


@torch.inference_mode()
def predict(model, x, batch_size=4096):
    param = next(model.parameters()); out = np.empty(len(x), dtype=np.float64)
    model.eval()
    for start in range(0, len(x), batch_size):
        z = torch.as_tensor(x[start:start+batch_size], dtype=param.dtype, device=param.device)
        out[start:start+len(z)] = torch.sigmoid(model(z)).squeeze(1).cpu().numpy()
    if not np.isfinite(out).all() or ((out < 0) | (out > 1)).any():
        raise ValueError('Invalid probabilities')
    return out
