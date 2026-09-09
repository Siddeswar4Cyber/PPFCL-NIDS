"""B2 training-only feature definitions and immutable-population overlap gates."""
import json
import tempfile
import time
import warnings
from pathlib import Path
import duckdb
import numpy as np
from sklearn.feature_selection import f_classif
from threadpoolctl import threadpool_limits
from audit_datasets import lit, write_json
from preprocess_p1 import sha, vector_sql
from run_baseline_pilot import ROOT, DATASETS, PROTOCOLS, bundle, load_partition

SHORTCUTS={
    'cic-ids-2017':['Destination Port','Init_Win_bytes_forward','Init_Win_bytes_backward','min_seg_size_forward'],
    'ND-UNSW-NB15-v3':['L4_SRC_PORT','L4_DST_PORT','PROTOCOL','L7_PROTO','MIN_TTL','MAX_TTL','TCP_WIN_MAX_IN','TCP_WIN_MAX_OUT','DNS_QUERY_ID']}
NOMINAL={'cic-ids-2017':['Destination Port'], 'ND-UNSW-NB15-v3':['L4_SRC_PORT','L4_DST_PORT','PROTOCOL','L7_PROTO']}
PERMUTATION_GROUPS={
    'cic-ids-2017':{'service':['Destination Port'], 'window_segment':['Init_Win_bytes_forward','Init_Win_bytes_backward','min_seg_size_forward'],
        'active_idle':['Active Mean','Active Std','Active Max','Active Min','Idle Mean','Idle Std','Idle Max','Idle Min']},
    'ND-UNSW-NB15-v3':{'service':['L4_SRC_PORT','L4_DST_PORT','PROTOCOL','L7_PROTO'],
        'ttl_window':['MIN_TTL','MAX_TTL','TCP_WIN_MAX_IN','TCP_WIN_MAX_OUT'],'dns_identifier':['DNS_QUERY_ID']}}


def field_columns(params, names):
    ids={p['input_id'] for p in params['parameters'] if p['name'] in names}
    found={p['name'] for p in params['parameters'] if p['name'] in names}
    if set(names)!=found: raise ValueError(f'Unknown fields: {set(names)-found}')
    return [i for i,n in enumerate(params['output_names']) if n.split('_')[0] in ids]


def define_features(dataset, params, x, y):
    width=len(params['output_names']); n=len(params['parameters'])
    assert x.shape==(len(y),width) and np.isfinite(x).all()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always'); scores,_=f_classif(x,y)
    scores=np.where(np.isfinite(scores),scores,0.0)
    ranking=[]
    for i,p in enumerate(params['parameters']):
        cols=field_columns(params,[p['name']])
        ranking.append({'name':p['name'],'input_id':p['input_id'],'columns':cols,'score':float(max(scores[cols])),'position':i})
    ranking.sort(key=lambda r:(-r['score'],r['position']))
    top=sorted(c for r in ranking[:min(32,n)] for c in r['columns'])
    removed=field_columns(params,SHORTCUTS[dataset]); categories=[]
    for i,p in enumerate(params['parameters']):
        if p['name'] not in NOMINAL[dataset]: continue
        # Exclude imputed values when fitting category frequency; missing flag remains in the original prefix.
        vals,counts=np.unique(x[x[:,n+i]==0,i],return_counts=True)
        order=sorted(range(len(vals)),key=lambda j:(-int(counts[j]),float(vals[j])))[:16]
        for j in order: categories.append({'column':i,'missing_column':n+i,'value':float(vals[j]),'training_count':int(counts[j]),'field':p['name']})
    definitions={'full':{'columns':list(range(width))},'no_shortcut':{'columns':[i for i in range(width) if i not in removed]},
        'top32':{'columns':top},'categorical_augmented':{'columns':list(range(width)),'categories':categories}}
    for d in definitions.values(): d['output_width']=len(d['columns'])+len(d.get('categories',[]))
    return definitions,ranking,[{'category':type(w.message).__name__,'message':str(w.message)} for w in caught]


def transform(x, definition):
    columns=definition['columns']
    if columns!=sorted(set(columns)) or not columns or max(columns)>=x.shape[1] or min(columns)<0: raise ValueError('Invalid feature projection')
    z=x[:,columns]
    if definition.get('categories'):
        indicators=[((x[:,c['column']]==c['value']) & (x[:,c['missing_column']]==0)).astype(np.float64) for c in definition['categories']]
        z=np.column_stack([z,*indicators])
        assert np.array_equal(z[:,:x.shape[1]],x),'Augmentation changed the original prefix'
    assert z.shape[1]==definition['output_width'] and np.isfinite(z).all()
    return z


def overlap_gate(con, columns, dtype):
    expr='['+','.join(f'vector[{i+1}]' for i in columns)+']'
    if dtype=='float32': expr=f'list_transform({expr},v->cast(v AS FLOAT))'
    con.execute(f'CREATE TABLE reduced AS SELECT group_id,primary_role,stress_role,{expr} AS z FROM projected')
    try:
        bad=con.execute('SELECT count(*) FROM reduced WHERE NOT list_bool_and(list_transform(z,v->isfinite(v)))').fetchone()[0]
        row=con.execute('''SELECT count(*),coalesce(sum(n),0),coalesce(sum(p>1),0),coalesce(sum(s>1),0) FROM
            (SELECT count(*) n,count(DISTINCT primary_role) p,count(DISTINCT stress_role) s FROM reduced GROUP BY z HAVING count(*)>1)''').fetchone()
        return {'dtype':dtype,'nonfinite_vectors':bad,'merged_vectors':row[0],'implicated_groups':row[1],
            'cross_primary_role_vectors':row[2],'cross_stress_role_vectors':row[3],'status':'PASSED' if bad==0 and row[0]==0 else 'REJECTED_UNDER_S1'}
    finally: con.execute('DROP TABLE reduced')


def main():
    for dataset in DATASETS:
        for protocol in PROTOCOLS:
            out=ROOT/'reports/cp6/features'/f'{dataset}-{protocol}.json'
            if out.exists(): raise RuntimeError(f'Refusing overwrite: {out}')
            began=time.perf_counter(); version,pipe,params=bundle(dataset,protocol)
            with threadpool_limits(limits=2):
                x,y,_=load_partition(dataset,protocol,'train',pipe,len(params['output_names']))
                definitions,ranking,warnings_=define_features(dataset,params,x,y)
            report_path=ROOT/'reports/preprocessing'/('cic-ids-2017-P2.json' if version=='P2' else dataset+'.json')
            cleaned=json.loads(report_path.read_text())['cleaned']; assert sha(cleaned['path'])==cleaned['sha256']
            result={'dataset':dataset,'protocol':protocol,'version':'B2','status':'RUNNING','script_sha256':sha(__file__),
                'preprocessing_version':version,'transform_sha256':pipe['transform_sha256'],'fit_group_set_sha256':pipe['fit_group_set_sha256'],
                'training_artifact':pipe['artifacts']['train'],'cleaned':cleaned,'training_only_ranking':ranking,'ranking_warnings':warnings_,
                'definitions':definitions,'population_changed':False}
            write_json(out,result)
            with tempfile.TemporaryDirectory(prefix='ppfcl-b2-gate-') as temp:
                con=duckdb.connect(str(Path(temp)/'work.duckdb'))
                try:
                    con.execute("SET memory_limit='4GB'"); con.execute('SET threads=4')
                    con.execute(f"CREATE VIEW cleaned AS SELECT * FROM read_parquet({lit(cleaned['path'])})")
                    con.execute(f'CREATE TABLE projected AS SELECT group_id,primary_role,stress_role,{vector_sql(params)} AS vector FROM cleaned WHERE quality_eligible AND representative')
                    result['all_role_representatives']=con.execute('SELECT count(*) FROM projected').fetchone()[0]
                    for variant,d in definitions.items():
                        print(f'{dataset}/{protocol}/{variant}: gate',flush=True)
                        if variant in ['full','categorical_augmented']:
                            transform(x,d)
                            d['gate']={'status':'PASSED','basis':'Verified B1 full vector; injective unchanged prefix for augmentation','float64':'PASSED','float32':'PASSED'}
                        else:
                            checks=[overlap_gate(con,d['columns'],dtype) for dtype in ['float64','float32']]
                            d['gate']={'status':'PASSED' if all(c['status']=='PASSED' for c in checks) else 'REJECTED_UNDER_S1','checks':checks}
                        print(json.dumps(d['gate']),flush=True); write_json(out,result)
                finally: con.close()
            result.update(status='COMPLETED',elapsed_seconds=time.perf_counter()-began); write_json(out,result)


if __name__=='__main__': main()
