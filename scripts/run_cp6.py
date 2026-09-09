"""B2 bounded feature comparisons and model-randomness sensitivity workers."""
import argparse
import json
import os
import subprocess
import sys
import time
import warnings
from pathlib import Path
import joblib
import numpy as np
import psutil
import sklearn
from threadpoolctl import threadpool_limits
from audit_datasets import write_json
from preprocess_p1 import sha
from baseline_metrics import evaluate, threshold_for_fpr
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, bundle, load_partition, make_model, model_complexity, identity as b1_identity
from cp6_features import transform

MODELS=['logistic','extra_trees','mlp']


def feature_spec(dataset,protocol):
    path=ROOT/'reports/cp6/features'/f'{dataset}-{protocol}.json'
    spec=json.loads(path.read_text()); assert spec['status']=='COMPLETED'
    assert spec['script_sha256']==sha(ROOT/'scripts/cp6_features.py')
    _,pipe,_=bundle(dataset,protocol)
    assert spec['transform_sha256']==pipe['transform_sha256'] and spec['fit_group_set_sha256']==pipe['fit_group_set_sha256']
    return spec,path


def identity(dataset,protocol,model,variant,seed): return f'B2-{dataset}-{protocol}-{model}-{variant}-s{seed}'


def worker(dataset,protocol,kind,variant,seed):
    began=time.perf_counter(); run_id=identity(dataset,protocol,kind,variant,seed)
    output=ROOT/'reports/cp6/runs'/f'{run_id}.json'; folder=ROOT/'models/B2'/dataset/protocol/kind/variant/f's{seed}'
    if output.exists() or folder.exists(): raise RuntimeError(f'Refusing overwrite: {run_id}')
    spec,spec_path=feature_spec(dataset,protocol); definition=spec['definitions'][variant]
    if definition['gate']['status']!='PASSED': raise ValueError('Representation rejected under S1')
    folder.mkdir(parents=True)
    result={'run_id':run_id,'experiment_id':'EXP-003','architecture_version':'A0','version':'B2','status':'RUNNING','dataset':dataset,'protocol':protocol,
        'model_kind':kind,'representation':variant,'seed':seed,'preregistration_commit':'6734173','git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'script_sha256':sha(__file__),'features_script_sha256':sha(ROOT/'scripts/cp6_features.py'),
        'baseline_script_sha256':sha(ROOT/'scripts/run_baseline_pilot.py'),'metrics_script_sha256':sha(ROOT/'scripts/baseline_metrics.py'),
        'feature_spec_path':str(spec_path),'feature_spec_sha256':sha(spec_path),'client_configuration':'Centralized CPU',
        'privacy_configuration':'Non-private development only','cl_configuration':'No CL model training'}
    write_json(output,result)
    try:
        with threadpool_limits(limits=2):
            version,pipe,params=bundle(dataset,protocol); width=len(params['output_names']); tick=time.perf_counter()
            x,y,labels=load_partition(dataset,protocol,'train',pipe,width); xv,yv,lv=load_partition(dataset,protocol,'validation',pipe,width)
            x=transform(x,definition); xv=transform(xv,definition)
            if kind=='extra_trees': x=x.astype(np.float32); xv=xv.astype(np.float32)
            model=make_model(kind).set_params(random_state=seed)
            result.update(preprocessing_version=version,split_version='S1',train_rows=len(y),validation_rows=len(yv),input_features=x.shape[1],
                input_artifacts=pipe['artifacts'],fit_group_set_sha256=pipe['fit_group_set_sha256'],transform_sha256=pipe['transform_sha256'],
                hyperparameters=model.get_params(),effective_input_dtype=str(x.dtype),load_seconds=time.perf_counter()-tick,
                environment={'python':sys.version.split()[0],'sklearn':sklearn.__version__,'numpy':np.__version__},hardware='reports/audit/environment.json')
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always'); tick=time.perf_counter(); model.fit(x,y); fit_seconds=time.perf_counter()-tick
            result['warnings']=[{'category':type(w.message).__name__,'message':str(w.message)} for w in caught]
            assert list(model.classes_)==[0,1]
            tick=time.perf_counter(); p=model.predict_proba(xv)[:,1]; prediction_seconds=time.perf_counter()-tick
            universe=sorted(set(json.loads((ROOT/'reports/splits/contracts'/f'{dataset}.json').read_text())['raw_to_canonical_label'].values()))
            calibrated=evaluate(yv,p,lv,universe,threshold_for_fpr(yv,p))
            assert calibrated['confusion']['fp']<=int(0.01*int((yv==0).sum()))
            model_path=folder/'model.joblib'; pred_path=folder/'validation-probabilities.npy'
            joblib.dump({'model':model,'definition':definition,'base_transform_sha256':pipe['transform_sha256']},model_path,compress=3)
            restored=joblib.load(model_path)
            delta=float(np.max(np.abs(restored['model'].predict_proba(xv[:256])[:,1]-p[:256])))
            assert delta<=1e-12
            np.save(pred_path,p,allow_pickle=False)
            batch=xv[:4096]; model.predict_proba(batch); times=[]
            for _ in range(7):
                tick=time.perf_counter(); model.predict_proba(batch); times.append((time.perf_counter()-tick)*1000)
            result.update(status='COMPLETED',fit_seconds=fit_seconds,validation_prediction_seconds=prediction_seconds,
                metrics_05=evaluate(yv,p,lv,universe,0.5),metrics_fpr01=calibrated,iterations=np.asarray(getattr(model,'n_iter_',[])).tolist(),
                loss_curve=getattr(model,'loss_curve_',[]),complexity=model_complexity(model),model_roundtrip_max_abs_delta=delta,
                latency={'batch_rows':len(batch),'warmup_batches':1,'repetitions':7,'batch_p50_ms':float(np.percentile(times,50)),'batch_p95_ms':float(np.percentile(times,95))},
                model_artifact={'path':str(model_path),'sha256':sha(model_path),'bytes':model_path.stat().st_size},
                validation_predictions={'path':str(pred_path),'sha256':sha(pred_path),'rows':len(p)},final_test_accessed=False,external_test_accessed=False)
    except Exception as exc:
        result.update(status='FAILED',error=repr(exc)); raise
    finally:
        result['worker_seconds']=time.perf_counter()-began; write_json(output,result)


def select_representation(candidates):
    full=next(r for r in candidates if r['representation']=='full'); m=full['metrics_05']
    eligible=[r for r in candidates if r['representation']!='full' and r['metrics_05']['binary_macro_f1']-m['binary_macro_f1']>=.002
        and r['metrics_05']['average_precision']>=m['average_precision']-.002]
    return min(eligible,key=lambda r:(-r['metrics_05']['binary_macro_f1'],-r['metrics_05']['average_precision'],r['input_features'],r['representation'])) if eligible else full


def select():
    output=ROOT/'reports/cp6/selection.json'
    if output.exists(): raise RuntimeError('Selection is frozen; refusing overwrite')
    selected=[]
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            spec,_=feature_spec(dataset,protocol)
            for kind in MODELS:
                bpath=ROOT/'reports/baselines/runs'/f'{b1_identity(dataset,protocol,kind)}.json'
                full=json.loads(bpath.read_text()); full['representation']='full'; candidates=[full]; bindings=[{'path':str(bpath),'sha256':sha(bpath)}]
                for variant,d in spec['definitions'].items():
                    if variant=='full' or d['gate']['status']!='PASSED': continue
                    path=ROOT/'reports/cp6/runs'/f'{identity(dataset,protocol,kind,variant,17)}.json'
                    r=json.loads(path.read_text()); assert r['status']=='COMPLETED' and r['exit_code']==0
                    assert r['fit_group_set_sha256']==full['fit_group_set_sha256'] and r['transform_sha256']==full['transform_sha256']
                    candidates.append(r); bindings.append({'path':str(path),'sha256':sha(path)})
                winner=select_representation(candidates)
                selected.append({'dataset':dataset,'protocol':protocol,'model_kind':kind,'representation':winner['representation'],
                    'seed17_run_id':winner['run_id'],'candidate_reports':bindings,
                    'rule':'Improve full macro-F1 by >=0.002 and lose <=0.002 AP; rank macro-F1/AP/width/name; otherwise retain full'})
    write_json(output,{'version':'B2','status':'FROZEN_FOR_SEED_SENSITIVITY','script_sha256':sha(__file__),'selected':selected})
    print('Frozen representation selection for 12 model/namespace combinations',flush=True)


def supervise(config):
    dataset,protocol,kind,variant,seed=config; run_id=identity(*config); output=ROOT/'reports/cp6/runs'/f'{run_id}.json'
    if output.exists():
        r=json.loads(output.read_text())
        if r['status']=='COMPLETED' and r.get('exit_code')==0 and r['script_sha256']==sha(__file__) and sha(r['validation_predictions']['path'])==r['validation_predictions']['sha256']:
            print(f'{run_id}: verified existing completion',flush=True); return
        raise RuntimeError(f'Existing incomplete or changed run requires review: {run_id}')
    log=ROOT/'reports/cp6/logs'/f'{run_id}.log'; log.parent.mkdir(parents=True,exist_ok=True)
    print(f'{run_id}: START',flush=True); began=time.perf_counter(); peak=0; stopped=None
    env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    with log.open('w',encoding='utf-8') as handle:
        proc=subprocess.Popen([sys.executable,'-u',str(Path(__file__)),'worker','--dataset',dataset,'--protocol',protocol,'--model',kind,'--variant',variant,'--seed',str(seed)],
            cwd=ROOT,env=env,stdout=handle,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        observed=psutil.Process(proc.pid)
        while proc.poll() is None:
            try:
                tree=[observed]+observed.children(recursive=True); rss=0
                for member in tree:
                    try: rss+=member.memory_info().rss
                    except psutil.NoSuchProcess: pass
                peak=max(peak,rss)
            except psutil.NoSuchProcess: break
            if peak>12*2**30 or time.perf_counter()-began>600:
                stopped='RSS or wall-time cap exceeded'
                for member in reversed(tree):
                    try: member.kill()
                    except psutil.NoSuchProcess: pass
                break
            time.sleep(.5)
        code=proc.wait()
    r=json.loads(output.read_text()) if output.exists() else {'run_id':run_id,'status':'FAILED'}
    r.update(exit_code=code,sampled_peak_process_rss_bytes=peak,supervised_wall_seconds=time.perf_counter()-began,
        rss_scope='Sum of worker and descendants, sampled every 0.5s',resource_limit_stop=stopped,log=str(log))
    if code!=0 or stopped: r.update(status='FAILED',supervisor_error=stopped or 'Worker failed')
    write_json(output,r); print(f'{run_id}: {r["status"]}',flush=True)
    if r['status']!='COMPLETED': raise RuntimeError(f'Preserve failed run and investigate: {run_id}')


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['worker','explore','select','confirm'])
    parser.add_argument('--dataset',choices=DATASETS); parser.add_argument('--protocol',choices=PROTOCOLS); parser.add_argument('--model',choices=MODELS)
    parser.add_argument('--variant',choices=['full','no_shortcut','top32','categorical_augmented']); parser.add_argument('--seed',type=int,choices=[17,29,43]); args=parser.parse_args()
    if args.stage=='worker': return worker(args.dataset,args.protocol,args.model,args.variant,args.seed)
    if args.stage=='select': return select()
    jobs=[]
    if args.stage=='explore':
        for dataset in DATASETS:
            for protocol in PROTOCOLS:
                spec,_=feature_spec(dataset,protocol)
                for variant,d in spec['definitions'].items():
                    if variant=='full' or d['gate']['status']!='PASSED': continue
                    for kind in MODELS: jobs.append((dataset,protocol,kind,variant,17))
    else:
        selection=json.loads((ROOT/'reports/cp6/selection.json').read_text()); assert selection['status']=='FROZEN_FOR_SEED_SENSITIVITY'
        assert selection['script_sha256']==sha(__file__)
        for r in selection['selected']:
            for binding in r['candidate_reports']: assert sha(binding['path'])==binding['sha256']
            for seed in [29,43]: jobs.append((r['dataset'],r['protocol'],r['model_kind'],r['representation'],seed))
    for job in jobs: supervise(job)


if __name__=='__main__': main()
