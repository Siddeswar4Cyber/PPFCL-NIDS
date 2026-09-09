"""B1 sequential CPU workers with sealed-input allowlist and resource caps."""
from __future__ import annotations
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
import pyarrow.parquet as pq
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from threadpoolctl import threadpool_limits,threadpool_info
from audit_datasets import write_json
from preprocess_p1 import sha
from baseline_metrics import evaluate,threshold_for_fpr

ROOT=Path(__file__).resolve().parents[1]
DATASETS=['cic-ids-2017','ND-UNSW-NB15-v3']; PROTOCOLS=['primary','stress']; MODELS=['prior','logistic','extra_trees','mlp']


def bundle(dataset,protocol):
    if dataset not in DATASETS or protocol not in PROTOCOLS: raise ValueError('Disallowed model namespace')
    version='P2' if dataset=='cic-ids-2017' else 'P1'
    if version=='P2': assert json.loads((ROOT/'reports/preprocessing/P2-verification.json').read_text())['status']=='PASSED'
    path=ROOT/'reports/preprocessing'/('cic-ids-2017-P2.json' if version=='P2' else dataset+'.json')
    r=json.loads(path.read_text()); assert r['status']=='COMPLETED'
    pipe=next(p for p in r['pipelines'] if p['protocol']==protocol)
    params=json.loads(Path(pipe['transform_path']).read_text()); assert sha(pipe['transform_path'])==pipe['transform_sha256']
    gate=pipe['float32_gate'] if version=='P2' else next(p for p in json.loads((ROOT/'reports/baselines/precision'/f'{dataset}.json').read_text()) if p['protocol']==protocol)
    assert gate['status']=='PASSED'
    return version,pipe,params


def load_partition(dataset,protocol,partition,pipe,width,features=True):
    if partition not in ['train','validation']: raise ValueError('Final/private/external inputs are sealed')
    version='P2' if dataset=='cic-ids-2017' else 'P1'
    path=ROOT/'data/processed'/version/dataset/protocol/(partition+'.parquet')
    artifact=pipe['artifacts'][partition]
    assert path.resolve()==Path(artifact['path']).resolve() and sha(path)==artifact['sha256']
    file=pq.ParquetFile(path); n=file.metadata.num_rows
    x=np.empty((n,width),dtype=np.float64) if features else None
    y=np.empty(n,dtype=np.uint8); labels=np.empty(n,dtype=object); cursor=0
    columns=['binary_label','label']+(['vector'] if features else [])
    for batch in file.iter_batches(batch_size=8192,columns=columns,use_threads=False):
        count=batch.num_rows; end=cursor+count
        y[cursor:end]=batch.column('binary_label').to_numpy(); labels[cursor:end]=batch.column('label').to_numpy(zero_copy_only=False)
        if features:
            a=batch.column('vector'); assert not a.null_count
            x[cursor:end]=a.flatten().to_numpy(zero_copy_only=False).reshape(count,width)
        cursor=end
    assert cursor==n and np.isin(y,[0,1]).all() and np.array_equal(labels!='benign',y.astype(bool))
    if features: assert np.isfinite(x).all()
    return x,y,labels


def make_model(kind):
    if kind=='prior': return DummyClassifier(strategy='prior',random_state=17)
    if kind=='logistic': return LogisticRegression(C=1,l1_ratio=0,solver='lbfgs',max_iter=500,tol=1e-4,random_state=17)
    if kind=='extra_trees': return ExtraTreesClassifier(n_estimators=64,max_depth=20,max_leaf_nodes=4096,min_samples_leaf=2,max_features='sqrt',n_jobs=4,random_state=17)
    if kind=='mlp': return MLPClassifier(hidden_layer_sizes=(64,32),activation='relu',solver='adam',alpha=0.0001,batch_size=256,learning_rate_init=0.001,max_iter=10,early_stopping=False,tol=0,n_iter_no_change=11,random_state=17)
    raise ValueError('Unknown model')


def identity(dataset,protocol,kind): return f'B1-{dataset}-{protocol}-{kind}-s17'


def model_complexity(model):
    result={}
    if hasattr(model,'coefs_'): result['parameters']=int(sum(a.size for a in model.coefs_+model.intercepts_))
    if hasattr(model,'coef_'): result['parameters']=int(model.coef_.size+model.intercept_.size)
    if hasattr(model,'estimators_'): result.update(nodes=int(sum(t.tree_.node_count for t in model.estimators_)),leaves=int(sum(t.tree_.n_leaves for t in model.estimators_)))
    return result


def worker(dataset,protocol,kind):
    began=time.perf_counter(); run_id=identity(dataset,protocol,kind)
    output=ROOT/'reports/baselines/runs'/f'{run_id}.json'
    folder=ROOT/'models/B1'/dataset/protocol/kind
    if folder.exists(): raise RuntimeError(f'Refusing overwrite of {folder}')
    folder.mkdir(parents=True)
    result={'run_id':run_id,'experiment_id':'EXP-003','dataset':dataset,'protocol':protocol,'model_kind':kind,'seed':17,'status':'RUNNING',
            'script_sha256':sha(__file__),'metrics_script_sha256':sha(ROOT/'scripts/baseline_metrics.py'),'git_commit':None}
    write_json(output,result)
    try:
        with threadpool_limits(limits=2):
            version,pipe,params=bundle(dataset,protocol); width=len(params['output_names'])
            tick=time.perf_counter(); x,y,labels=load_partition(dataset,protocol,'train',pipe,width)
            xv,yv,lv=load_partition(dataset,protocol,'validation',pipe,width)
            assert len(y)==100000
            result.update(preprocessing_version=version,split_version='S1',train_rows=len(y),validation_rows=len(yv),input_features=width,
                fit_group_set_sha256=pipe['fit_group_set_sha256'],transform_sha256=pipe['transform_sha256'],input_artifacts=pipe['artifacts'],
                load_seconds=time.perf_counter()-tick,environment={'python':sys.version.split()[0],'sklearn':sklearn.__version__,'numpy':np.__version__,'threadpools':threadpool_info()},
                hardware='reports/audit/environment.json',class_support={'train':{label:int((labels==label).sum()) for label in sorted(set(labels))},'validation':{label:int((lv==label).sum()) for label in sorted(set(lv))}})
            model=make_model(kind); result['hyperparameters']=model.get_params()
            if kind=='extra_trees': x=x.astype(np.float32); xv=xv.astype(np.float32)
            result['effective_input_dtype']=str(x.dtype)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always'); tick=time.perf_counter(); model.fit(x,y); fit_seconds=time.perf_counter()-tick
            result['warnings']=[{'category':type(w.message).__name__,'message':str(w.message)} for w in caught]
            assert np.array_equal(model.classes_,[0,1])
            tick=time.perf_counter(); probabilities=model.predict_proba(xv)[:,1]; prediction_seconds=time.perf_counter()-tick
            universe=sorted(set(json.loads((ROOT/'reports/splits/contracts'/f'{dataset}.json').read_text())['raw_to_canonical_label'].values()))
            threshold=threshold_for_fpr(yv,probabilities,0.01)
            default=evaluate(yv,probabilities,lv,universe,0.5); calibrated=evaluate(yv,probabilities,lv,universe,threshold)
            assert calibrated['confusion']['fp']<=int(0.01*int((yv==0).sum()))
            model_path=folder/'model.joblib'; joblib.dump(model,model_path,compress=3)
            restored=joblib.load(model_path)
            restored_p=restored.predict_proba(xv[:256])[:,1]
            assert np.allclose(restored_p,probabilities[:256],rtol=1e-12,atol=1e-12),'Model roundtrip mismatch'
            result['model_roundtrip_max_abs_delta']=float(np.max(np.abs(restored_p-probabilities[:256])))
            prediction_path=folder/'validation-probabilities.npy'; np.save(prediction_path,probabilities,allow_pickle=False)
            latency=[]; batch=xv[:4096]; model.predict_proba(batch)
            for _ in range(7):
                tick=time.perf_counter(); model.predict_proba(batch); latency.append((time.perf_counter()-tick)*1000)
            complexity=model_complexity(model)
            result.update(status='COMPLETED',fit_seconds=fit_seconds,validation_prediction_seconds=prediction_seconds,metrics_05=default,metrics_fpr01=calibrated,
                iterations=np.asarray(getattr(model,'n_iter_',[])).tolist(),loss_curve=getattr(model,'loss_curve_',[]),complexity=complexity,
                latency={'batch_rows':len(batch),'warmup_batches':1,'repetitions':7,'batch_p50_ms':float(np.percentile(latency,50)),'batch_p95_ms':float(np.percentile(latency,95)),'measurements_ms':latency},
                model_artifact={'path':str(model_path.resolve()),'sha256':sha(model_path),'bytes':model_path.stat().st_size},
                validation_predictions={'path':str(prediction_path.resolve()),'sha256':sha(prediction_path),'rows':len(probabilities)},
                final_test_accessed=False,external_test_accessed=False,model_roundtrip_verified=True)
    except Exception as exc:
        result.update(status='FAILED',error=repr(exc)); raise
    finally:
        result['worker_seconds']=time.perf_counter()-began; write_json(output,result)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--worker',action='store_true'); parser.add_argument('--dataset',choices=DATASETS); parser.add_argument('--protocol',choices=PROTOCOLS); parser.add_argument('--model',choices=MODELS); args=parser.parse_args()
    if args.worker: return worker(args.dataset,args.protocol,args.model)
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            bundle(dataset,protocol)
            for kind in MODELS:
                run_id=identity(dataset,protocol,kind); output=ROOT/'reports/baselines/runs'/f'{run_id}.json'
                if output.exists(): raise RuntimeError(f'Existing run must be explicitly reviewed: {run_id}')
                log=ROOT/'reports/baselines/logs'/f'{run_id}.log'; log.parent.mkdir(parents=True,exist_ok=True)
                print(f'{run_id}: START',flush=True); began=time.perf_counter(); peak=0; stopped=None
                env=dict(os.environ,OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',OMP_NUM_THREADS='2')
                with log.open('w',encoding='utf-8') as handle:
                    proc=subprocess.Popen([sys.executable,'-u',str(Path(__file__)),'--worker','--dataset',dataset,'--protocol',protocol,'--model',kind],cwd=ROOT,env=env,stdout=handle,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    observed=psutil.Process(proc.pid)
                    while proc.poll() is None:
                        try:
                            process_tree=[observed]+observed.children(recursive=True)
                            rss=0
                            for member in process_tree:
                                try: rss+=member.memory_info().rss
                                except psutil.NoSuchProcess: pass
                            peak=max(peak,rss)
                        except psutil.NoSuchProcess: break
                        if peak>12*2**30 or time.perf_counter()-began>600:
                            stopped='RSS or wall-time cap exceeded'
                            for member in reversed(process_tree):
                                try: member.kill()
                                except psutil.NoSuchProcess: pass
                            break
                        time.sleep(0.5)
                    code=proc.wait()
                result=json.loads(output.read_text()) if output.exists() else {'run_id':run_id,'status':'FAILED'}
                result.update(sampled_peak_process_rss_bytes=peak,rss_scope='Worker process tree, including Windows launcher; sampled every 0.5s',supervised_wall_seconds=time.perf_counter()-began,exit_code=code,log=str(log.relative_to(ROOT)),resource_limit_stop=stopped)
                if code!=0: result.update(status='FAILED',supervisor_error=stopped or 'Worker failed; see log')
                write_json(output,result)
                print(f'{run_id}: {result["status"]}',flush=True)
                if result['status']!='COMPLETED': raise RuntimeError(f'{run_id} failed; preserve evidence and investigate')


if __name__=='__main__': main()
