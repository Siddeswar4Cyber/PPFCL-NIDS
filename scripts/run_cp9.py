"""F1 bounded centralized, routed-local and FedAvg/client-Adam simulation."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import numpy as np
import psutil
import pyarrow.compute as pc
import pyarrow.parquet as pq
import torch
from threadpoolctl import threadpool_limits
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, load_partition
from run_cp8 import context, binding, read
from build_clients_c1 import SCENARIOS, META, metadata
from cp6_features import transform
from baseline_metrics import evaluate, threshold_for_fpr
from neural_runtime import configure, network, predict
from federated_f1 import state_copy, state_digest, aggregate, epoch_order, update


def ident(dataset,protocol,method,scenario): return f'F1-{dataset}-{protocol}-{method}-{scenario}-s17'


def contract(dataset,protocol,scenario,pipe):
    path=ROOT/'reports/cp7/clients'/f'{dataset}-{protocol}-{scenario}.json'; r=read(path)
    verification=read(ROOT/'reports/cp7/verification.json'); assert verification['status']=='PASSED'
    b=next(b for b in verification['report_bindings'] if Path(b['path']).resolve()==path.resolve())
    assert sha(path)==b['sha256'] and sha(r['artifact']['path'])==r['artifact']['sha256']
    assert r['parent_artifacts']==pipe['artifacts'] and r['transform_sha256']==pipe['transform_sha256']
    table=pq.read_table(r['artifact']['path']); owners={}
    for partition in ['train','validation']:
        part=table.filter(pc.equal(table['partition'],partition)); parent=metadata(pipe['artifacts'][partition])
        assert part.select(META).equals(parent)
        assert np.array_equal(part['row_index'].to_numpy(),np.arange(len(parent)))
        o=part['client_id'].to_numpy(); assert np.isin(o,np.arange(5)).all(); owners[partition]=o
        y=parent['binary_label'].to_numpy()
        for i in range(5):
            support=next(s for s in r['support'] if s['partition']==partition and s['client_id']==i)
            mask=o==i; assert int(mask.sum())==support['rows']
            assert int(((y==0)&mask).sum())==support['benign'] and int(((y==1)&mask).sum())==support['attack']
            assert support['benign']>=20 and support['attack']>=20
    return owners,r,binding(path)


def score(y,p,labels,universe,owners=None):
    threshold=threshold_for_fpr(y,p); result={'metrics_05':evaluate(y,p,labels,universe),
        'metrics_fpr01':evaluate(y,p,labels,universe,threshold)}
    if owners is not None:
        clients=[]
        for i in range(5):
            mask=owners==i
            clients.append({'client_id':i,'metrics_05':evaluate(y[mask],p[mask],labels[mask],universe),
                'metrics_common_threshold':evaluate(y[mask],p[mask],labels[mask],universe,threshold)})
        f=np.array([c['metrics_05']['binary_macro_f1'] for c in clients]); sizes=np.bincount(owners,minlength=5)
        result.update(clients=clients,client_macro_f1={'mean':float(f.mean()),'validation_weighted_mean':float(np.average(f,weights=sizes)),
            'minimum':float(f.min()),'population_sd':float(f.std(ddof=0))})
    assert result['metrics_fpr01']['confusion']['fp']<=int(.01*int((y==0).sum()))
    return result


def worker(dataset,protocol,method,scenario):
    run_id=ident(dataset,protocol,method,scenario); out=ROOT/'reports/cp9/runs'/f'{run_id}.json'; folder=ROOT/'models/F1'/run_id
    if out.exists() or folder.exists(): raise RuntimeError('Refusing overwrite: '+run_id)
    folder.mkdir(parents=True); started=time.perf_counter()
    r={'run_id':run_id,'version':'F1','experiment_id':'EXP-004','architecture_version':'A0','dataset':dataset,'protocol':protocol,
        'method':method,'scenario':scenario,'seed':17,'status':'RUNNING','script_sha256':sha(__file__),
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_bindings':[binding(ROOT/p) for p in ['scripts/federated_f1.py','scripts/neural_runtime.py','scripts/run_cp8.py',
            'scripts/run_baseline_pilot.py','scripts/cp6_features.py','scripts/baseline_metrics.py','scripts/build_clients_c1.py',
            'tests/test_federated_f1.py','docs/CP9-federated-pilot-F1.md','reports/cp8/verification.json',
            'reports/cp8/selection.json','reports/cp7/verification.json','requirements-neural-lock.txt']],
        'privacy_configuration':'Non-private single-process synthetic-client simulation; no DP or secure aggregation',
        'cl_configuration':'No CL','final_test_accessed':False,'external_test_accessed':False,
        'environment':{'torch':str(torch.__version__),'numpy':np.__version__,'python':sys.version.split()[0]},'work':[]}
    write_json(out,r)
    try:
        configure()
        with threadpool_limits(limits=2):
            verification=read(ROOT/'reports/cp8/verification.json'); assert verification['status']=='PASSED'
            assert sha(verification['selection']['path'])==verification['selection']['sha256']
            selection=next(s for s in read(verification['selection']['path'])['scopes'] if s['dataset']==dataset and s['protocol']==protocol)
            assert selection['status']=='PILOT_ELIGIBLE'
            lr=next(c['learning_rate'] for c in selection['candidates'] if c['candidate']==selection['selected_candidate'])
            version,pipe,params,definition,_,meta=context(dataset,protocol)
            x,y,_=load_partition(dataset,protocol,'train',pipe,len(params['output_names']))
            xv,yv,lv=load_partition(dataset,protocol,'validation',pipe,len(params['output_names']))
            x=transform(x,definition).astype(np.float32); xv=transform(xv,definition).astype(np.float32)
            assert len(y)==100000
            ownership=None
            if method!='central':
                ownership,c1,b=contract(dataset,protocol,scenario,pipe)
                r.update(client_contract=b,client_membership=c1['artifact'],actual_client_method=c1['actual_method'])
                ids=[np.flatnonzero(ownership['train']==i) for i in range(5)]
            else: ids=[np.arange(len(y))]
            counts=[len(i) for i in ids]; assert all(math.ceil(n/256)<=400 for n in counts)
            assert sum(counts)==100000
            init=state_copy(network(x.shape[1])); initial_path=folder/'initial.pt'; torch.save(init,initial_path)
            states=[{k:v.clone() for k,v in init.items()} for _ in ids]
            global_state={k:v.clone() for k,v in init.items()}
            tensors=[(torch.as_tensor(x[i],device='cuda'),torch.as_tensor(y[i].astype(np.float32),device='cuda')) for i in ids]
            r.update(meta,preprocessing_version=version,input_artifacts=pipe['artifacts'],transform_sha256=pipe['transform_sha256'],
                fit_group_set_sha256=pipe['fit_group_set_sha256'],input_features=x.shape[1],train_rows=len(y),validation_rows=len(yv),
                client_train_rows=counts,initial_weights=binding(initial_path),rounds=[],
                hyperparameters={'learning_rate':lr,'epochs_or_rounds':20,'local_epochs_per_round':1,'batch_size':256,
                    'regularizer_lambda':.0001/256,'weight_only':True,'optimizer':'Native Adam, reset every epoch/round',
                    'betas':[.9,.999],'eps':1e-8,'weight_decay':0,'foreach':False,'fused':False,'server_optimizer':None,
                    'participation':1.0,'aggregation':'n_k/N weighted float64 sum then float32' if method=='fedavg' else None})
            torch.cuda.synchronize(); tick=time.perf_counter()
            for epoch in range(1,21):
                uploads=[]
                for i,(xt,yt) in enumerate(tensors):
                    client=-1 if method=='central' else i
                    order=epoch_order(len(yt),dataset,protocol,scenario,epoch,client)
                    start=global_state if method=='fedavg' else states[i]
                    before={k:v.clone() for k,v in start.items()}
                    final,work=update(start,xt,yt,lr,order)
                    assert all(torch.equal(start[k],before[k]) for k in before),'Client mutated round start'
                    work.update(epoch=epoch,client_id=client,start_state_sha256=state_digest(before),end_state_sha256=state_digest(final),
                        global_row_order_sha256=hashlib.sha256(np.asarray(ids[i][order],dtype='<i8').tobytes()).hexdigest())
                    r['work'].append(work); uploads.append(final)
                    if method!='fedavg': states[i]=final
                if method=='fedavg':
                    averaged=aggregate(uploads,counts); round_path=folder/f'round-{epoch:02d}.pt'
                    torch.save({'round_start':global_state,'uploads':uploads,'training_counts':counts,'aggregated':averaged},round_path)
                    r['rounds'].append({'round':epoch,'artifact':binding(round_path)}); global_state=averaged
                print(f'epoch/round {epoch}/20 completed',flush=True)
            torch.cuda.synchronize(); r['fit_seconds']=time.perf_counter()-tick
            final_states=[global_state] if method=='fedavg' else states
            paths=[]; p=np.empty(len(yv),dtype=np.float64); tick=time.perf_counter()
            for i,state in enumerate(final_states):
                model=network(x.shape[1],device='cuda'); model.load_state_dict(state)
                model_path=folder/f'model-{i}.pt'; torch.save(state,model_path); paths.append(binding(model_path))
                mask=ownership['validation']==i if method=='local' else np.ones(len(yv),dtype=bool)
                p[mask]=predict(model,xv[mask])
            r['prediction_seconds']=time.perf_counter()-tick
            universe=sorted(set(read(ROOT/'reports/splits/contracts'/f'{dataset}.json')['raw_to_canonical_label'].values()))
            pred_path=folder/'validation-probabilities.npy'; np.save(pred_path,p,allow_pickle=False)
            r.update(final_models=paths,validation_predictions=binding(pred_path),
                evaluation=score(yv,p,lv,universe,None if ownership is None else ownership['validation']))
            r['examples_seen']=sum(w['rows'] for w in r['work']); r['optimizer_steps']=sum(w['steps'] for w in r['work'])
            assert r['examples_seen']==2000000
            parameter_count=sum(v.numel() for v in init.values()); payload=4*parameter_count
            r.update(parameter_count=parameter_count,communication={'kind':'Calculated float32 tensor payload; not measured network',
                'upload_bytes':payload*5*20 if method=='fedavg' else None,
                'download_bytes':payload*5*20 if method=='fedavg' else None,
                'includes_biases':True,'includes_protocol_or_crypto':False,'raw_data_transfer_estimated':False})
        r['status']='COMPLETED'
    except Exception as exc:
        r.update(status='FAILED',error=repr(exc)); raise
    finally:
        r.update(worker_seconds=time.perf_counter()-started,cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(0),
            cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(0))
        write_json(out,r)


def supervise(dataset,protocol,method,scenario):
    run_id=ident(dataset,protocol,method,scenario); out=ROOT/'reports/cp9/runs'/f'{run_id}.json'
    if out.exists():
        r=read(out); assert r['status']=='COMPLETED' and r['exit_code']==0 and r['script_sha256']==sha(__file__)
        for b in r['source_bindings']: assert sha(b['path'])==b['sha256']
        print(run_id+': verified existing completion',flush=True); return
    spent=sum(read(p).get('supervised_wall_seconds',0) for p in (ROOT/'reports/cp9/runs').glob('*.json'))
    if spent+600>14400: raise RuntimeError('EXP-004 four-hour family budget cannot reserve another worker')
    log=ROOT/'reports/cp9/logs'/f'{run_id}.log'; log.parent.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter(); peak=0; stopped=None
    env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',CUBLAS_WORKSPACE_CONFIG=':4096:8')
    print(run_id+': START',flush=True)
    with log.open('w',encoding='utf-8') as handle:
        proc=subprocess.Popen([sys.executable,'-u',__file__,'worker','--dataset',dataset,'--protocol',protocol,
            '--method',method,'--scenario',scenario],cwd=ROOT,env=env,stdout=handle,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        observed=psutil.Process(proc.pid)
        while proc.poll() is None:
            tree=[observed]
            try:
                tree+=observed.children(recursive=True); rss=0
                for member in tree:
                    try: rss+=member.memory_info().rss
                    except psutil.NoSuchProcess: pass
                peak=max(peak,rss)
            except psutil.NoSuchProcess: pass
            if peak>12*2**30 or time.perf_counter()-started>600:
                stopped='Worker-tree RSS or wall-time cap exceeded'
                for member in reversed(tree):
                    try: member.kill()
                    except psutil.NoSuchProcess: pass
                break
            time.sleep(.5)
        code=proc.wait()
    r=read(out) if out.exists() else {'run_id':run_id,'status':'FAILED'}
    r.update(exit_code=code,sampled_peak_process_rss_bytes=peak,supervised_wall_seconds=time.perf_counter()-started,
        rss_scope='Worker and descendants sampled every 0.5 seconds',resource_limit_stop=stopped,log=str(log))
    if code!=0 or stopped: r['status']='FAILED'
    write_json(out,r); print(run_id+': '+r['status'],flush=True)
    if r['status']!='COMPLETED': raise RuntimeError('Preserve failed run and investigate: '+run_id)


def main():
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['all','worker'])
    p.add_argument('--dataset',choices=DATASETS); p.add_argument('--protocol',choices=PROTOCOLS)
    p.add_argument('--method',choices=['central','local','fedavg']); p.add_argument('--scenario',choices=['all',*SCENARIOS]); a=p.parse_args()
    if a.action=='worker':
        if not all([a.dataset,a.protocol,a.method,a.scenario]): p.error('Worker needs all scope fields')
        if (a.method=='central') != (a.scenario=='all'): p.error('Only central uses scenario all')
        worker(a.dataset,a.protocol,a.method,a.scenario); return
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            supervise(dataset,protocol,'central','all')
            for scenario in SCENARIOS:
                for method in ['local','fedavg']: supervise(dataset,protocol,method,scenario)


if __name__=='__main__': main()
