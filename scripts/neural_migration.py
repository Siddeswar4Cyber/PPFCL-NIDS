"""Prediction-only MLP migration helpers; importing this module does not require Torch."""
import numpy as np
from scipy.special import expit


def validate_model(model):
    if (tuple(model.hidden_layer_sizes) != (64, 32) or model.activation != 'relu'
            or model.out_activation_ != 'logistic' or list(model.classes_) != [0, 1]):
        raise ValueError('Unsupported MLP architecture or class ordering')
    widths = [model.n_features_in_, 64, 32, 1]
    if len(model.coefs_) != 3 or len(model.intercepts_) != 3:
        raise ValueError('Expected three affine layers')
    for i, (w, b) in enumerate(zip(model.coefs_, model.intercepts_)):
        if w.shape != (widths[i], widths[i+1]) or b.shape != (widths[i+1],):
            raise ValueError('Invalid weight or bias shape')
        if not np.isfinite(w).all() or not np.isfinite(b).all():
            raise ValueError('Nonfinite parameters')


def numpy_predict(model, x, batch_size=4096):
    validate_model(model)
    if batch_size < 1 or x.ndim != 2 or x.shape[1] != model.n_features_in_:
        raise ValueError('Invalid input shape or batch size')
    out = np.empty(len(x), dtype=np.float64)
    for start in range(0, len(x), batch_size):
        z = np.asarray(x[start:start+batch_size], dtype=np.float64)
        if not np.isfinite(z).all():
            raise ValueError('Nonfinite inputs')
        for i, (w, b) in enumerate(zip(model.coefs_, model.intercepts_)):
            z = z @ w + b
            if i < 2:
                z = np.maximum(z, 0)
        out[start:start+len(z)] = expit(z[:, 0])
    return out


def to_torch(model, device='cpu', dtype=None):
    """Copy parameters, not optimizer state; must pass runtime gates before use."""
    validate_model(model)
    import torch
    dtype = torch.float64 if dtype is None else dtype
    network = torch.nn.Sequential(
        torch.nn.Linear(model.n_features_in_, 64), torch.nn.ReLU(),
        torch.nn.Linear(64, 32), torch.nn.ReLU(), torch.nn.Linear(32, 1)
    ).to(device=device, dtype=dtype)
    with torch.no_grad():
        for layer, w, b in zip((network[0], network[2], network[4]), model.coefs_, model.intercepts_):
            layer.weight.copy_(torch.as_tensor(w.T, dtype=dtype, device=device))
            layer.bias.copy_(torch.as_tensor(b, dtype=dtype, device=device))
    return network.eval()  # Forward returns logits; callers must apply sigmoid.
