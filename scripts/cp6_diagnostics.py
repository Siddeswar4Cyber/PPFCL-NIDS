"""B2 validation-only permutation sensitivity and NF endpoint overlap."""
import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
import duckdb
import joblib
import numpy as np
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits
from audit_datasets import lit, write_json, load_file, fetch_dict
from preprocess_p1 import sha
from baseline_metrics import evaluate
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, bundle, load_partition, identity
from cp6_features import PERMUTATION_GROUPS, field_columns


def baseline(dataset,protocol,kind):
    path=ROOT/'reports/baselines/runs'/f'{identity(dataset,protocol,kind)}.json'; r=json.loads(path.read_text())
    assert r['status']=='COMPLETED' and r['exit_code']==0
    for key in ['model_artifact','validation_predictions']: assert sha(r[key]['path'])==r[key]['sha256']
    return r


def permutation():
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            output=ROOT/'reports/cp6/diagnostics'/f'{dataset}-{protocol}-permutation.json'
            if output.exists(): raise RuntimeError(f'Refusing overwrite {output}')
            began=time.perf_counter(); _,pipe,params=bundle(dataset,protocol)
            with threadpool_limits(limits=2):
                x,y,labels=load_partition(dataset,protocol,'validation',pipe,len(params['output_names']))
                indices=np.sort(np.random.default_rng(17).choice(len(y),min(50000,len(y)),replace=False))
                x=x[indices]; y=y[indices]; labels=labels[indices]
                universe=sorted(set(json.loads((ROOT/'reports/splits/contracts'/f'{dataset}.json').read_text())['raw_to_canonical_label'].values()))
                runs=[]
                for kind in ['extra_trees','mlp']:
                    r=baseline(dataset,protocol,kind); model=joblib.load(r['model_artifact']['path'])
                    if kind=='extra_trees': xin=x.astype(np.float32)
                    else: xin=x
                    p=model.predict_proba(xin)[:,1]
                    assert np.allclose(p,np.load(r['validation_predictions']['path'],allow_pickle=False)[indices],rtol=1e-12,atol=1e-12)
                    control=evaluate(y,p,labels,universe,.5); arrays={'row_indices':indices,'control':p}; changes=[]
                    for group,names in PERMUTATION_GROUPS[dataset].items():
                        cols=field_columns(params,names)
                        for seed in [17,29,43]:
                            order=np.random.default_rng(seed).permutation(len(y)); z=xin.copy(); z[:,cols]=xin[order][:,cols]
                            perturbed=model.predict_proba(z)[:,1]; key=f'{group}_s{seed}'; arrays[key]=perturbed
                            metrics=evaluate(y,perturbed,labels,universe,.5)
                            changes.append({'group':group,'fields':names,'columns':cols,'permutation_seed':seed,'array_key':key,'metrics_05':metrics,
                                'macro_f1_drop':control['binary_macro_f1']-metrics['binary_macro_f1'],
                                'average_precision_drop':control['average_precision']-metrics['average_precision']})
                    path=ROOT/'data/diagnostics/B2'/dataset/protocol/f'{kind}-permutation.npz'; path.parent.mkdir(parents=True,exist_ok=True)
                    if path.exists(): raise RuntimeError(f'Refusing overwrite {path}')
                    np.savez_compressed(path,**arrays)
                    runs.append({'model_kind':kind,'baseline_run_id':r['run_id'],'model_sha256':r['model_artifact']['sha256'],
                        'control_metrics_05':control,'changes':changes,'saved_predictions':{'path':str(path),'sha256':sha(path)}})
                    print(f'{dataset}/{protocol}/{kind}: grouped permutation complete',flush=True)
            write_json(output,{'version':'B2','dataset':dataset,'protocol':protocol,'status':'COMPLETED','script_sha256':sha(__file__),
                'validation_artifact':pipe['artifacts']['validation'],'subset_rows':len(indices),'selection_seed':17,
                'row_indices_sha256':hashlib.sha256(indices.astype('<i8').tobytes()).hexdigest(),'runs':runs,'elapsed_seconds':time.perf_counter()-began,
                'interpretation':'Marginal joint-group permutation sensitivity; potentially unrealistic combinations; not causal or retrained ablation scores',
                'final_test_accessed':False,'external_test_accessed':False})


def hosts():
    dataset='ND-UNSW-NB15-v3'; output=ROOT/'reports/cp6/diagnostics/NF-host-overlap.json'
    if output.exists(): raise RuntimeError(f'Refusing overwrite {output}')
    began=time.perf_counter(); contract=json.loads((ROOT/'reports/splits/contracts'/f'{dataset}.json').read_text())
    source=contract['source_files'][0]; assert sha(source['path'])==source['sha256']
    results=[]
    with tempfile.TemporaryDirectory(prefix='ppfcl-b2-host-') as temp:
        con=duckdb.connect(str(Path(temp)/'work.duckdb'))
        try:
            con.execute("SET memory_limit='4GB'"); con.execute('SET threads=4'); con.execute('SET preserve_insertion_order=true')
            info=load_file(con,Path(source['path']),source,contract['columns'],0,False); assert info['error_events']==0
            for protocol in PROTOCOLS:
                _,pipe,params=bundle(dataset,protocol)
                for part in ['train','validation']: assert sha(pipe['artifacts'][part]['path'])==pipe['artifacts'][part]['sha256']
                con.execute('DROP TABLE IF EXISTS joined')
                parts=[f"SELECT {lit(part)} AS partition,row_number() OVER () AS ordinal,source_file,parsed_row,binary_label FROM read_parquet({lit(pipe['artifacts'][part]['path'])})" for part in ['train','validation']]
                con.execute(f'''CREATE TABLE joined AS SELECT m.*,nullif(trim(r.c002),'') AS src,nullif(trim(r.c004),'') AS dst,
                    try_cast(r.c053 AS INTEGER) AS original_label FROM ({' UNION ALL '.join(parts)}) m JOIN raw r USING(source_file,parsed_row)''')
                nval=pq.ParquetFile(pipe['artifacts']['validation']['path']).metadata.num_rows
                assert con.execute('SELECT count(*) FROM joined').fetchone()[0]==100000+nval
                assert con.execute('SELECT count(*) FROM joined WHERE binary_label IS DISTINCT FROM original_label').fetchone()[0]==0
                con.execute('DROP TABLE IF EXISTS training_hosts'); con.execute('DROP TABLE IF EXISTS training_pairs')
                con.execute("CREATE TABLE training_hosts AS SELECT src AS host FROM joined WHERE partition='train' AND src IS NOT NULL UNION SELECT dst FROM joined WHERE partition='train' AND dst IS NOT NULL")
                con.execute("CREATE TABLE training_pairs AS SELECT DISTINCT src,dst FROM joined WHERE partition='train' AND src IS NOT NULL AND dst IS NOT NULL")
                con.execute('DROP TABLE IF EXISTS masks')
                con.execute('''CREATE TABLE masks AS SELECT v.ordinal,v.source_file,v.parsed_row,v.binary_label,
                    v.src IS NULL OR v.dst IS NULL AS missing_endpoint,
                    s.host IS NOT NULL AND d.host IS NOT NULL AS both_hosts_seen,
                    p.src IS NOT NULL AS ordered_pair_seen
                    FROM joined v LEFT JOIN training_hosts s ON s.host=v.src LEFT JOIN training_hosts d ON d.host=v.dst
                    LEFT JOIN training_pairs p ON p.src=v.src AND p.dst=v.dst WHERE v.partition='validation' ORDER BY v.ordinal''')
                path=ROOT/'data/diagnostics/B2'/dataset/protocol/'host-masks.parquet'; path.parent.mkdir(parents=True,exist_ok=True)
                if path.exists(): raise RuntimeError(f'Refusing overwrite {path}')
                con.execute(f'COPY (SELECT * FROM masks ORDER BY ordinal) TO {lit(str(path))} (FORMAT PARQUET, COMPRESSION ZSTD)')
                table=pq.read_table(path); missing=table['missing_endpoint'].to_numpy(); seen=table['ordered_pair_seen'].to_numpy(); hosts_seen=table['both_hosts_seen'].to_numpy()
                _,y,labels=load_partition(dataset,protocol,'validation',pipe,len(params['output_names']),features=False)
                assert np.array_equal(y,table['binary_label'].to_numpy())
                universe=sorted(set(contract['raw_to_canonical_label'].values()))
                groups={'seen_ordered_pair':seen & ~missing,'unseen_ordered_pair':~seen & ~missing,
                    'both_hosts_seen':hosts_seen & ~missing,'at_least_one_unseen_host':~hosts_seen & ~missing,'missing_endpoint':missing}
                metrics=[]
                for kind in ['logistic','extra_trees','mlp']:
                    r=baseline(dataset,protocol,kind); p=np.load(r['validation_predictions']['path'],allow_pickle=False)
                    for group,mask in groups.items():
                        metrics.append({'model_kind':kind,'subgroup':group,'rows':int(mask.sum()),'metrics_05':evaluate(y[mask],p[mask],labels[mask],universe,.5) if mask.any() else None})
                nh=con.execute('SELECT count(*) FROM training_hosts').fetchone()[0]; npairs=con.execute('SELECT count(*) FROM training_pairs').fetchone()[0]
                unique_val=con.execute("SELECT count(*),count(*) FILTER(WHERE host IN (SELECT host FROM training_hosts)) FROM (SELECT src AS host FROM joined WHERE partition='validation' AND src IS NOT NULL UNION SELECT dst FROM joined WHERE partition='validation' AND dst IS NOT NULL)").fetchone()
                results.append({'protocol':protocol,'training_unique_hosts':nh,'training_unique_ordered_pairs':npairs,
                    'validation_unique_hosts':unique_val[0],'validation_unique_hosts_seen_in_train':unique_val[1],
                    'validation_rows':len(y),'missing_endpoint_rows':int(missing.sum()),'both_hosts_seen_rows':int((hosts_seen & ~missing).sum()),
                    'ordered_pair_seen_rows':int((seen & ~missing).sum()),'subgroup_metrics':metrics,
                    'masks':{'path':str(path),'sha256':sha(path)},'input_artifacts':pipe['artifacts']})
                print(f'NF/{protocol}: {nh} training hosts; {int(seen.sum())}/{len(y)} validation rows share ordered pairs',flush=True)
        finally: con.close()
    write_json(output,{'version':'B2','status':'COMPLETED','script_sha256':sha(__file__),'source_sha256':source['sha256'],
        'results':results,'elapsed_seconds':time.perf_counter()-began,'final_test_accessed':False,'external_test_accessed':False,
        'interpretation':'Metadata overlap diagnostic only; no IP predictors, host-only classifier or independent-host evaluation'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['permutation','hosts']); args=parser.parse_args()
    permutation() if args.stage=='permutation' else hosts()
