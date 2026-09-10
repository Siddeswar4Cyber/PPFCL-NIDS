"""F1 source/work/round reconstruction and final-prediction comparison."""
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np
import torch
from sklearn.metrics import f1_score
from threadpoolctl import threadpool_limits
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT,DATASETS,PROTOCOLS,load_partition
from run_cp8 import context,read,binding
from run_cp9 import ident,contract,score
from build_clients_c1 import SCENARIOS
from cp6_features import transform
from neural_runtime import configure,network,predict


def digest(state):
    h=hashlib.sha256()
    for key,tensor in state.items():
        h.update(key.encode()+b'\0'+str(tuple(tensor.shape)).encode()+str(tensor.dtype).encode())
        h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def verify_common(path):
    r=read(path)
    assert r['status']=='COMPLETED' and r['exit_code']==0 and r['resource_limit_stop'] is None
    assert r['script_sha256']==sha(ROOT/'scripts/run_cp9.py')
    for b in r['source_bindings']+r['bindings']+[r['initial_weights'],r['validation_predictions']]+r['final_models']:
        assert sha(b['path'])==b['sha256'],b['path']
    assert not r['final_test_accessed'] and not r['external_test_accessed']
    assert r['sampled_peak_process_rss_bytes']<=12*2**30 and r['cuda_peak_reserved_bytes']<=4*2**30
    assert r['supervised_wall_seconds']<=601 and r['train_rows']==100000 and r['examples_seen']==2000000
    assert r['optimizer_steps']==sum(w['steps'] for w in r['work'])
    h=r['hyperparameters']
    assert h['regularizer_lambda']==.0001/256 and h['weight_only']
    assert h['epochs_or_rounds']==20 and h['local_epochs_per_round']==1 and h['batch_size']==256
    assert h['betas']==[.9,.999] and h['eps']==1e-8 and h['weight_decay']==0
    assert not h['foreach'] and not h['fused'] and h['server_optimizer'] is None and h['participation']==1.
    assert h['optimizer']=='Native Adam, reset every epoch/round'
    return r


def verify_work(r,owners):
    initial=torch.load(r['initial_weights']['path'],weights_only=True,map_location='cpu')
    expected=network(r['input_features']).state_dict()
    assert list(initial)==list(expected) and all(torch.equal(initial[k],expected[k]) for k in initial)
    ids=[np.arange(100000)] if owners is None else [np.flatnonzero(owners==i) for i in range(5)]
    assert r['client_train_rows']==[len(i) for i in ids]
    assert len(r['work'])==20*len(ids)
    last={}; order_hashes=[]
    for epoch in range(1,21):
        for i,rows in enumerate(ids):
            client=-1 if owners is None else i
            w=r['work'][(epoch-1)*len(ids)+i]
            assert (w['epoch'],w['client_id'],w['rows'],w['steps'])==(epoch,client,len(rows),math.ceil(len(rows)/256))
            assert w['steps']<=400 and np.isfinite(w['mean_training_objective'])
            tag=f'F1|17|{r["dataset"]}|{r["protocol"]}|{r["scenario"]}|{epoch}|{client}'
            seed=int(hashlib.sha256(tag.encode()).hexdigest()[:16],16)
            order=np.random.default_rng(seed).permutation(len(rows))
            assert np.array_equal(np.sort(rows[order]),rows)
            assert w['order_sha256']==hashlib.sha256(order.astype('<i8').tobytes()).hexdigest()
            assert w['global_row_order_sha256']==hashlib.sha256(rows[order].astype('<i8').tobytes()).hexdigest()
            order_hashes.append(w['global_row_order_sha256'])
            if epoch==1: assert w['start_state_sha256']==digest(initial)
            if r['method']!='fedavg' and epoch>1: assert w['start_state_sha256']==last[client]
            last[client]=w['end_state_sha256']
    if r['method']=='fedavg':
        assert len(r['rounds'])==20
        previous=initial
        for epoch,entry in enumerate(r['rounds'],1):
            assert entry['round']==epoch and sha(entry['artifact']['path'])==entry['artifact']['sha256']
            saved=torch.load(entry['artifact']['path'],weights_only=True,map_location='cpu')
            assert all(torch.equal(saved['round_start'][k],previous[k]) for k in previous)
            assert saved['training_counts']==r['client_train_rows'] and len(saved['uploads'])==5
            work=r['work'][(epoch-1)*5:epoch*5]
            for i,state in enumerate(saved['uploads']):
                assert list(state)==list(initial)
                assert work[i]['start_state_sha256']==digest(previous) and work[i]['end_state_sha256']==digest(state)
            for key in initial:
                expected=np.zeros(tuple(initial[key].shape),dtype=np.float64)
                for state,n in zip(saved['uploads'],saved['training_counts']):
                    x=state[key].numpy(); assert x.dtype==np.float32 and x.shape==expected.shape and np.isfinite(x).all()
                    expected+=x.astype(np.float64)*(n/100000)
                assert np.array_equal(expected.astype(np.float32),saved['aggregated'][key].numpy()),'Weighted aggregation mismatch'
            previous=saved['aggregated']
        final=torch.load(r['final_models'][0]['path'],weights_only=True,map_location='cpu')
        assert all(torch.equal(final[k],previous[k]) for k in initial)
        param_count=sum(t.numel() for t in final.values())
        assert r['parameter_count']==param_count
        assert r['communication']['upload_bytes']==r['communication']['download_bytes']==param_count*4*5*20
    else:
        for i,b in enumerate(r['final_models']):
            final=torch.load(b['path'],weights_only=True,map_location='cpu')
            assert digest(final)==last[-1 if owners is None else i]
        assert r['communication']['upload_bytes'] is None and r['communication']['download_bytes'] is None
    return order_hashes


def verify_predictions(r,xv,yv,lv,universe,owners):
    p=np.load(r['validation_predictions']['path'],allow_pickle=False); expected=np.empty(len(yv),dtype=np.float64)
    assert p.shape==yv.shape and len(r['final_models'])==(5 if r['method']=='local' else 1)
    for i,b in enumerate(r['final_models']):
        model=network(xv.shape[1],device='cuda')
        model.load_state_dict(torch.load(b['path'],weights_only=True,map_location='cpu'))
        mask=owners==i if r['method']=='local' else np.ones(len(yv),dtype=bool)
        expected[mask]=predict(model,xv[mask])
    assert np.array_equal(p,expected)
    actual=score(yv,p,lv,universe,owners)
    assert actual==r['evaluation']
    assert abs(float(f1_score(yv,p>=.5,labels=[0,1],average='macro'))-actual['metrics_05']['binary_macro_f1'])<1e-12
    return p,actual


def main():
    out=ROOT/'reports/cp9/verification.json'; comparison_path=ROOT/'reports/cp9/comparison.json'
    if out.exists() or comparison_path.exists(): raise RuntimeError('Preserve existing verification/comparison')
    started=time.perf_counter(); configure()
    test_path=ROOT/'reports/cp9/tests.log'; log=test_path.read_text(encoding='utf-8')
    assert 'Ran 36 tests' in log and log.strip().endswith('OK')
    targeted=ROOT/'reports/cp9/f1-tests.log'; target_log=targeted.read_text(encoding='utf-8')
    assert 'Ran 4 tests' in target_log and target_log.strip().endswith('OK')
    report={'status':'RUNNING','script_sha256':sha(__file__),'test_log':binding(test_path),'targeted_test_log':binding(targeted),'tests_passed':36,
        'report_bindings':[],'checks':[],'final_test_accessed':False,'external_test_accessed':False}
    comparison={'version':'F1','status':'COMPLETED','seed':17,'comparisons':[],
        'interpretation':'Exploratory single-seed C1 simulation, not a winning-method decision or privacy guarantee'}
    with threadpool_limits(limits=2):
        for dataset in DATASETS:
            for protocol in PROTOCOLS:
                _,pipe,params,definition,_,_=context(dataset,protocol)
                xv,yv,lv=load_partition(dataset,protocol,'validation',pipe,len(params['output_names']))
                xv=transform(xv,definition).astype(np.float32)
                universe=sorted(set(read(ROOT/'reports/splits/contracts'/f'{dataset}.json')['raw_to_canonical_label'].values()))
                path=ROOT/'reports/cp9/runs'/f'{ident(dataset,protocol,"central","all")}.json'
                central=verify_common(path); assert central['input_artifacts']==pipe['artifacts']
                selected=next(s for s in read(ROOT/'reports/cp8/selection.json')['scopes'] if s['dataset']==dataset and s['protocol']==protocol)
                expected_lr=next(c['learning_rate'] for c in selected['candidates'] if c['candidate']==selected['selected_candidate'])
                assert central['hyperparameters']['learning_rate']==expected_lr and central['representation']==selected['representation']
                verify_work(central,None); pcen,_=verify_predictions(central,xv,yv,lv,universe,None)
                report['report_bindings'].append(binding(path)); report['checks'].append({'run_id':central['run_id'],'status':'PASSED'})
                for scenario in SCENARIOS:
                    owners,c1,c1binding=contract(dataset,protocol,scenario,pipe)
                    central_view=score(yv,pcen,lv,universe,owners['validation']); modes={}; orders={}
                    for method in ['local','fedavg']:
                        path=ROOT/'reports/cp9/runs'/f'{ident(dataset,protocol,method,scenario)}.json'
                        r=verify_common(path)
                        assert r['client_contract']==c1binding and r['client_membership']==c1['artifact']
                        assert r['actual_client_method']==c1['actual_method'] and r['input_artifacts']==pipe['artifacts']
                        assert r['hyperparameters']['learning_rate']==central['hyperparameters']['learning_rate']
                        orders[method]=verify_work(r,owners['train'])
                        _,modes[method]=verify_predictions(r,xv,yv,lv,universe,owners['validation'])
                        report['report_bindings'].append(binding(path)); report['checks'].append({'run_id':r['run_id'],'status':'PASSED',
                            'full_predictions_reproduced':True,'work_order_verified':True,'aggregation_rounds_verified':20 if method=='fedavg' else 0})
                    assert orders['local']==orders['fedavg']
                    local=modes['local']; fed=modes['fedavg']
                    delta=fed['metrics_05']['binary_macro_f1']-local['metrics_05']['binary_macro_f1']
                    worst=fed['client_macro_f1']['minimum']-local['client_macro_f1']['minimum']
                    comparison['comparisons'].append({'dataset':dataset,'protocol':protocol,'scenario':scenario,
                        'actual_client_method':c1['actual_method'],'client_contract':c1binding,'central':central_view,'local':local,'fedavg':fed,
                        'fedavg_minus_local_macro_f1':delta,'fedavg_minus_local_worst_client_macro_f1':worst,
                        'fedavg_minus_central_macro_f1':fed['metrics_05']['binary_macro_f1']-central_view['metrics_05']['binary_macro_f1'],
                        'exploratory_collaboration_signal':delta>=.002 and worst>=-.01})
                    print(f'{dataset}/{protocol}/{scenario}: 20 aggregations, paired orders and predictions verified',flush=True)
    assert len(report['checks'])==28 and len(comparison['comparisons'])==12
    spent=sum(read(b['path'])['supervised_wall_seconds'] for b in report['report_bindings']); assert spent<=14400
    write_json(comparison_path,comparison)
    report.update(status='PASSED',comparison=binding(comparison_path),supervised_model_worker_seconds=spent,
        four_hour_family_budget_remaining_seconds=14400-spent,elapsed_seconds=time.perf_counter()-started)
    write_json(out,report)


if __name__=='__main__': main()
