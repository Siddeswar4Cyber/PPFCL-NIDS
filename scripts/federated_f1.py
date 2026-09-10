"""F1 common objective, deterministic local updates and parameter-only averaging."""
import hashlib
import math
import numpy as np
import torch
from neural_runtime import network, optimizer


def state_copy(model):
    return {k: v.detach().cpu().clone() for k,v in model.state_dict().items()}


def state_digest(state):
    h=hashlib.sha256()
    for key,x in state.items():
        h.update(key.encode()+b'\0'+str(tuple(x.shape)).encode()+str(x.dtype).encode())
        h.update(x.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def aggregate(states, counts):
    if not states or len(states) != len(counts) or any(type(n) is not int or n <= 0 for n in counts):
        raise ValueError('Positive integer training counts and matching uploads required')
    keys = list(states[0]); out = {}; total = sum(counts)
    if not keys: raise ValueError('Empty parameter state')
    for state in states:
        if list(state) != keys: raise ValueError('Mismatched parameter keys/order')
    for key in keys:
        template = states[0][key]
        if template.dtype != torch.float32: raise ValueError('F1 uploads must be float32')
        accumulator = torch.zeros_like(template, dtype=torch.float64, device='cpu')
        for state,n in zip(states,counts):
            x = state[key]
            if x.shape != template.shape or x.dtype != template.dtype or not torch.isfinite(x).all():
                raise ValueError('Invalid upload shape/dtype/value')
            accumulator += x.detach().cpu().double()*(n/total)
        out[key] = accumulator.float()
    return out


def objective(model, x, y):
    data = torch.nn.functional.binary_cross_entropy_with_logits(model(x).squeeze(1), y)
    penalty = sum(layer.weight.square().sum() for layer in (model[0],model[2],model[4]))
    return data+(.5*.0001/256)*penalty


def epoch_order(n, dataset, protocol, scenario, epoch, client):
    tag = f'F1|17|{dataset}|{protocol}|{scenario}|{epoch}|{client}'
    seed = int(hashlib.sha256(tag.encode()).hexdigest()[:16],16)
    return np.random.default_rng(seed).permutation(n)


def update(start, x, y, lr, order):
    """One full epoch; fresh Adam. Caller-owned start is never mutated."""
    n = len(y)
    if n == 0 or math.ceil(n/256) > 400 or not np.array_equal(np.sort(order),np.arange(n)):
        raise ValueError('Epoch must visit each allowed row exactly once within the step cap')
    model = network(x.shape[1], device=x.device)
    model.load_state_dict(start); model.train(); opt = optimizer(model,lr)
    ids = torch.as_tensor(order, device=x.device); total_loss = torch.zeros((),dtype=torch.float64,device=x.device)
    for offset in range(0,n,256):
        batch = ids[offset:offset+256]; opt.zero_grad(set_to_none=True)
        loss = objective(model,x[batch],y[batch]); loss.backward(); opt.step()
        total_loss += loss.detach().double()*len(batch)
    final = state_copy(model); value = float((total_loss/n).item())
    if not np.isfinite(value) or not all(torch.isfinite(v).all() for v in final.values()):
        raise ValueError('Nonfinite update')
    return final, {'rows': n, 'steps': math.ceil(n/256), 'mean_training_objective': value,
                   'order_sha256': hashlib.sha256(np.asarray(order,dtype='<i8').tobytes()).hexdigest()}
