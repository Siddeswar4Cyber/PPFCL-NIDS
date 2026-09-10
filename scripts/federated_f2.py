"""F2 extensions: seed-compatible client Adam, proximal objective and server Adam."""
import hashlib
import math
import numpy as np
import torch
from neural_runtime import network, optimizer
from federated_f1 import objective, state_copy, update as f1_update


def epoch_order(n, dataset, protocol, scenario, epoch, client, seed=17):
    tag = f'F1|{seed}|{dataset}|{protocol}|{scenario}|{epoch}|{client}'
    return np.random.default_rng(int(hashlib.sha256(tag.encode()).hexdigest()[:16],16)).permutation(n)


def proximal_objective(model, x, y, anchor, mu):
    if not math.isfinite(mu) or mu < 0: raise ValueError('Invalid proximal coefficient')
    value=objective(model,x,y)
    if mu:
        value=value+(mu/2)*sum((p-anchor[k]).square().sum() for k,p in model.named_parameters())
    return value


def update(start, x, y, lr, order, mu=0.):
    if not math.isfinite(mu) or mu < 0: raise ValueError('Invalid proximal coefficient')
    if mu==0: return f1_update(start,x,y,lr,order)
    n=len(y)
    if n==0 or math.ceil(n/256)>400 or not np.array_equal(np.sort(order),np.arange(n)):
        raise ValueError('Invalid epoch coverage or cap')
    model=network(x.shape[1],device=x.device); model.load_state_dict(start); model.train()
    anchor={k:v.detach().to(x.device).clone() for k,v in start.items()}
    opt=optimizer(model,lr); ids=torch.as_tensor(order,device=x.device)
    total_loss=torch.zeros((),dtype=torch.float64,device=x.device)
    for offset in range(0,n,256):
        batch=ids[offset:offset+256]; opt.zero_grad(set_to_none=True)
        loss=proximal_objective(model,x[batch],y[batch],anchor,mu)
        loss.backward(); opt.step(); total_loss+=loss.detach().double()*len(batch)
    final=state_copy(model); value=float((total_loss/n).item())
    if not np.isfinite(value) or not all(torch.isfinite(v).all() for v in final.values()):
        raise ValueError('Nonfinite update')
    return final,{'rows':n,'steps':math.ceil(n/256),'mean_training_objective':value,
        'order_sha256':hashlib.sha256(np.asarray(order,dtype='<i8').tobytes()).hexdigest()}


def server_adam(start, averaged, moments, lr, beta1=.9, beta2=.99, tau=.001):
    if not (math.isfinite(lr) and lr>0 and 0<=beta1<1 and 0<=beta2<1 and math.isfinite(tau) and tau>0):
        raise ValueError('Invalid server hyperparameters')
    if not start or list(start)!=list(averaged): raise ValueError('Mismatched server states')
    if moments is None:
        moments={'m':{k:torch.zeros_like(v,dtype=torch.float64,device='cpu') for k,v in start.items()},
                 'v':{k:torch.full_like(v,tau*tau,dtype=torch.float64,device='cpu') for k,v in start.items()}}
    if set(moments)!={'m','v'} or any(list(moments[c])!=list(start) for c in ['m','v']):
        raise ValueError('Mismatched moments')
    out={}; after={'m':{},'v':{}}
    for k,s in start.items():
        a=averaged[k]; m=moments['m'][k]; v=moments['v'][k]
        if s.dtype!=torch.float32 or a.dtype!=torch.float32 or m.dtype!=torch.float64 or v.dtype!=torch.float64:
            raise ValueError('Invalid server dtype')
        if any(t.shape!=s.shape or not torch.isfinite(t).all() for t in [s,a,m,v]) or (v<0).any():
            raise ValueError('Invalid server shape/value')
        delta=a.detach().cpu().double()-s.detach().cpu().double()
        after['m'][k]=beta1*m+(1-beta1)*delta
        after['v'][k]=beta2*v+(1-beta2)*delta.square()
        out[k]=(s.detach().cpu().double()+lr*after['m'][k]/(after['v'][k].sqrt()+tau)).float()
        if not torch.isfinite(out[k]).all(): raise ValueError('Nonfinite server update')
    return out,after,moments
