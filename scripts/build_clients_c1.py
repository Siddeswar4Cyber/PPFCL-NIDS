"""C1 group-consistent logical clients on immutable development matrices."""
import hashlib
import json
import subprocess
import time
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, bundle

SCENARIOS={'iid':None,'dirichlet_a1':1.0,'dirichlet_a0p1':0.1}
N_CLIENTS=5
META=['source_file','parsed_row','group_id','label','binary_label','task_id','representative']


def group_uniform(groups,tag):
    return np.fromiter((int(hashlib.sha256((tag+'|'+g).encode()).hexdigest()[:13],16)/16**13 for g in groups),dtype=np.float64,count=len(groups))


def assign(uniform,labels,probabilities):
    owners=np.empty(len(labels),dtype=np.int8)
    for label in sorted(set(labels)):
        p=np.asarray(probabilities.get(label,[.2]*5),dtype=np.float64)
        if p.shape!=(5,) or (p<0).any() or not np.isfinite(p).all() or not np.isclose(p.sum(),1,atol=1e-12): raise ValueError('Invalid allocation probabilities')
        cdf=np.cumsum(p); cdf[-1]=1.0; mask=labels==label
        owners[mask]=np.searchsorted(cdf,uniform[mask],side='right')
    assert ((owners>=0)&(owners<5)).all()
    return owners


def binary_support(owners,y):
    return [{'client_id':i,'rows':int((owners==i).sum()),'benign':int(((owners==i)&(y==0)).sum()),'attack':int(((owners==i)&(y==1)).sum())} for i in range(5)]


def acceptable(support): return all(s['rows']>=1000 and s['benign']>=20 and s['attack']>=20 for s in support)


def choose(groups,labels,y,tag,alpha):
    u=group_uniform(groups,tag); labels_present=sorted(set(labels)); attempts=[]
    rng=np.random.default_rng(int(hashlib.sha256(tag.encode()).hexdigest()[:16],16))
    count=1 if alpha is None else 20
    for attempt in range(1,count+1):
        probabilities={label:([.2]*5 if alpha is None else rng.dirichlet(np.full(5,alpha)).tolist()) for label in labels_present}
        owners=assign(u,labels,probabilities); support=binary_support(owners,y); ok=acceptable(support)
        attempts.append({'attempt':attempt,'method':'uniform_iid' if alpha is None else 'pure_dirichlet','probabilities':probabilities,'training_support':support,'accepted':ok})
        if ok: return owners,probabilities,attempts
    if alpha is not None:
        probabilities={k:(.9*np.asarray(v)+.1/5).tolist() for k,v in probabilities.items()}
        owners=assign(u,labels,probabilities); support=binary_support(owners,y); ok=acceptable(support)
        attempts.append({'attempt':21,'method':'dirichlet_uniform10_fallback','probabilities':probabilities,'training_support':support,'accepted':ok})
        if ok: return owners,probabilities,attempts
    return None,None,attempts


def metadata(artifact):
    assert sha(artifact['path'])==artifact['sha256']
    return pq.read_table(artifact['path'],columns=META)


def describe(table,owners,universe,partition):
    labels=table['label'].to_numpy(); y=table['binary_label'].to_numpy(); groups=table['group_id'].to_numpy()
    result=[]
    for i,s in enumerate(binary_support(owners,y)):
        mask=owners==i
        result.append({**s,'partition':partition,'groups':len(set(groups[mask])),'fraction_of_partition':s['rows']/len(y),
            'attack_prevalence':s['attack']/s['rows'] if s['rows'] else None,
            'canonical_support':{label:int(((labels==label)&mask).sum()) for label in universe},
            'balanced_evaluation_eligible':s['benign']>=20 and s['attack']>=20 if partition=='validation' else None})
    return result


def main():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            version,pipe,_=bundle(dataset,protocol); tables={p:metadata(pipe['artifacts'][p]) for p in ['train','validation']}
            tr=tables['train']; assert len(tr)==100000 and len(set(tr['group_id'].to_pylist()))==len(tr)
            groups=tr['group_id'].to_numpy(); labels=tr['label'].to_numpy(); y=tr['binary_label'].to_numpy()
            universe=sorted(set(json.loads((ROOT/'reports/splits/contracts'/f'{dataset}.json').read_text())['raw_to_canonical_label'].values()))
            for scenario,alpha in SCENARIOS.items():
                began=time.perf_counter(); output=ROOT/'reports/cp7/clients'/f'{dataset}-{protocol}-{scenario}.json'
                folder=ROOT/'data/clients/C1'/dataset/protocol/scenario
                if output.exists() or folder.exists(): raise RuntimeError(f'Refusing overwrite {folder}')
                tag=f'C1|17|{dataset}|{protocol}|{scenario}'
                owners,probabilities,attempts=choose(groups,labels,y,tag,alpha)
                report={'version':'C1','run_id':f'C1-{dataset}-{protocol}-{scenario}','experiment_id':'EXP-004','dataset':dataset,'protocol':protocol,
                    'requested_scenario':scenario,'alpha':alpha,'seed':17,'scope_tag':tag,'clients':5,'status':'INFEASIBLE' if owners is None else 'COMPLETED',
                    'script_sha256':sha(__file__),'git_commit':commit,'preprocessing_version':version,'parent_artifacts':pipe['artifacts'],
                    'transform_sha256':pipe['transform_sha256'],'fit_group_set_sha256':pipe['fit_group_set_sha256'],'attempts':attempts,
                    'actual_method':attempts[-1]['method'] if owners is not None else None,'probabilities':probabilities,
                    'final_private_public_external_access':False,'validation_used_for_acceptance':False,
                    'interpretation':'Synthetic label-aware evaluation ownership; shared centralized development preprocessing; no host separation or privacy guarantee'}
                if owners is not None:
                    folder.mkdir(parents=True); parts=[]; support=[]
                    for partition,table in tables.items():
                        clients=owners if partition=='train' else assign(group_uniform(table['group_id'].to_numpy(),tag),table['label'].to_numpy(),probabilities)
                        support+=describe(table,clients,universe,partition)
                        parts.append(table.append_column('partition',pa.array([partition]*len(table))).append_column('row_index',pa.array(np.arange(len(table)),type=pa.int64())).append_column('client_id',pa.array(clients)))
                    path=folder/'memberships.parquet'; pq.write_table(pa.concat_tables(parts),path,compression='zstd')
                    report.update(artifact={'path':str(path),'sha256':sha(path),'rows':sum(len(t) for t in tables.values())},support=support)
                report['elapsed_seconds']=time.perf_counter()-began; write_json(output,report)
                print(f'{dataset}/{protocol}/{scenario}: {report["status"]}, {len(attempts)} attempt(s), {report["actual_method"]}',flush=True)


if __name__=='__main__': main()
