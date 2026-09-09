"""P1 baseline preparation: fit only permitted development representatives."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import tempfile
import threading
import time
from pathlib import Path
import duckdb
import psutil
from audit_datasets import fingerprint, load_file, lit, fetch_dict, write_json
from build_split_manifests import numeric_projection

ROOT=Path(__file__).resolve().parents[1]
VERSION='P1'
WINDOWS={'Init_Win_bytes_forward','Init_Win_bytes_backward'}
ALLOWED={'primary':'primary_role','stress':'stress_role','cl':'task_role'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(8*1024*1024): h.update(block)
    return h.hexdigest()


def cleaning_expressions(features):
    clean=[]; sentinels=[]; bad=[]
    for i,f in enumerate(features,1):
        v=f'x[{i}]'
        if f['name'] in WINDOWS:
            clean.append(f'nullif({v},-1)')
            sentinels.append(f'coalesce({v}=-1,false)::DOUBLE')
            bad.append(f'({v}<0 AND {v}<>-1)')
        else:
            clean.append(v); bad.append(f'{v}<0')
    return '['+','.join(clean)+']', '['+','.join(sentinels)+']::DOUBLE[]', 'coalesce('+ ' OR '.join(bad)+',false)'


def fitting_predicate(protocol):
    if protocol not in ALLOWED: raise ValueError('Unknown fitting scope')
    return f"quality_eligible AND representative AND {ALLOWED[protocol]}='development_train'"+(' AND task_id=1' if protocol=='cl' else '')


def fit_parameters(con, features, protocol, limit=100000):
    con.execute('DROP TABLE IF EXISTS fit')
    con.execute(f"CREATE TABLE fit AS SELECT * FROM cleaned WHERE {fitting_predicate(protocol)} ORDER BY sha256('pilot17|' || group_id),group_id LIMIT {int(limit)}")
    n=con.execute('SELECT count(*) FROM fit').fetchone()[0]
    if not n: raise RuntimeError('Empty permitted fitting sample')
    expr=[]
    for i in range(1,len(features)+1):
        expr += [f'median(clean_x[{i}])',f'max(abs(clean_x[{i}]))',f'count(clean_x[{i}])']
    stats=con.execute('SELECT '+','.join(expr)+' FROM fit').fetchone()
    params=[]
    for i,f in enumerate(features):
        median,maximum,observed=stats[3*i:3*i+3]
        maximum=maximum or 0.0
        if maximum<=1: scale=1.0
        else:
            m,e=math.frexp(maximum)
            scale=math.ldexp(1.0,e-1 if m==0.5 else e)
        if not math.isfinite(scale): raise RuntimeError('Unrepresentable scale')
        params.append({'input_id':f['id'],'name':f['name'],'median':median if median is not None else 0.0,
                       'all_missing_fallback':median is None,'observed_fit_rows':observed,'fit_max_abs':maximum,'scale':scale})
    fit_hash=hashlib.sha256()
    for (g,) in con.execute('SELECT group_id FROM fit ORDER BY group_id').fetchall(): fit_hash.update((g+'\n').encode('ascii'))
    return {'version':VERSION,'protocol':protocol,'fit_predicate':fitting_predicate(protocol),'fit_rows':n,
            'fit_label_support':fetch_dict(con,'SELECT label,binary_label,count(*) AS rows FROM fit GROUP BY ALL ORDER BY ALL'),
            'fit_group_set_sha256':fit_hash.hexdigest(),'sampling':'SHA256(pilot17|group_id),group_id; at most 100000 representatives',
            'parameters':params,'sentinel_fields':[f['name'] for f in features if f['name'] in WINDOWS],
            'output_names':[f['id']+'_scaled' for f in features]+[f['id']+'_missing' for f in features]+[f['id']+'_sentinel_minus1' for f in features if f['name'] in WINDOWS],
            'dtype':'float64','fit_role':'development_train','private_use':'NOT AUTHORIZED as a privacy-confirmatory preprocessing release'}


def vector_sql(params):
    values=[f"coalesce(clean_x[{i}],{p['median']!r})/{p['scale']!r}" for i,p in enumerate(params['parameters'],1)]
    values += [f'(clean_x[{i}] IS NULL)::DOUBLE' for i in range(1,len(params['parameters'])+1)]
    values += [f'sentinels[{i}]' for i in range(1,len(params['sentinel_fields'])+1)]
    return '['+','.join(values)+']::DOUBLE[]'


def verify_vectors(con, params):
    con.execute('DROP TABLE IF EXISTS transformed')
    con.execute(f'CREATE TABLE transformed AS SELECT group_id,{vector_sql(params)} AS vector FROM cleaned WHERE quality_eligible AND representative')
    finite=con.execute(f"SELECT count(*) FROM transformed WHERE len(vector)<>{len(params['output_names'])} OR list_count(vector)<>{len(params['output_names'])} OR NOT list_bool_and(list_transform(vector,v -> isfinite(v)))").fetchone()[0]
    if finite: raise RuntimeError(f'Nonfinite/wrong-shape vectors: {finite}')
    reverse=' AND '.join(f"(clean_x[{i}] IS NULL OR (clean_x[{i}]/{p['scale']!r})*{p['scale']!r}=clean_x[{i}])" for i,p in enumerate(params['parameters'],1))
    loss=con.execute(f'SELECT count(*) FROM cleaned WHERE quality_eligible AND representative AND NOT ({reverse})').fetchone()[0]
    if loss: raise RuntimeError(f'Scaling lost observed numeric precision: {loss}')
    merged=con.execute('SELECT count(*) FROM (SELECT vector FROM transformed GROUP BY vector HAVING count(*)>1)').fetchone()[0]
    if merged: raise RuntimeError(f'Transform merged distinct S1 groups: {merged}')
    return {'finite_shape_failures':finite,'observed_roundtrip_failures':loss,'merged_S1_groups':merged,
            'verified_groups':con.execute('SELECT count(*) FROM transformed').fetchone()[0]}


def family(name):
    began=time.perf_counter(); peak=[0]; done=threading.Event()
    def monitor():
        while not done.wait(1): peak[0]=max(peak[0],psutil.Process().memory_info().rss)
    thread=threading.Thread(target=monitor,daemon=True); thread.start()
    result={'version':VERSION,'dataset':name,'status':'RUNNING','pipelines':[]}
    report=ROOT/'reports/preprocessing'/f'{name}.json'
    destination=ROOT/'data/processed'/VERSION/name
    if destination.exists(): raise RuntimeError(f'Refusing to overwrite {destination}')
    destination.mkdir(parents=True)
    try:
        split=json.loads((ROOT/'reports/splits'/f'{name}.json').read_text())
        manifest=Path(split['manifest_path']); cpath=manifest.parent/'contract.json'
        assert sha(manifest)==split['manifest_sha256'] and sha(cpath)==split['contract_sha256']
        contract=json.loads(cpath.read_text()); features=contract['predictors']
        result.update(source_manifest_sha256=split['manifest_sha256'],contract_sha256=split['contract_sha256'],
                      script_sha256=sha(Path(__file__)),environment={'duckdb':duckdb.__version__,'memory_limit':'4GB','threads':8})
        with tempfile.TemporaryDirectory(prefix='ppfcl-preprocess-') as temp:
            con=duckdb.connect(str(Path(temp)/'work.duckdb'))
            try:
                con.execute("SET memory_limit='4GB'"); con.execute('SET threads=8'); con.execute('SET preserve_insertion_order=true')
                for i,f in enumerate(contract['source_files']):
                    print(f'{name}: verify/stage {Path(f["path"]).name}',flush=True)
                    assert fingerprint(Path(f['path']))['sha256']==f['sha256']
                    assert load_file(con,Path(f['path']),f,contract['columns'],f['source_file'],i>0)['error_events']==0
                con.execute(f"CREATE VIEW memberships AS SELECT * FROM read_parquet({lit(str(manifest))})")
                con.execute('CREATE TABLE normalized AS SELECT source_file,parsed_row,['+','.join(numeric_projection(f['id']) for f in features)+']::DOUBLE[] AS x FROM raw')
                con.execute('DROP TABLE raw')
                assert con.execute("SELECT count(*) FROM normalized JOIN memberships USING(source_file,parsed_row) WHERE sha256('S1|17|' || to_json(x))<>group_id").fetchone()[0]==0
                clean,sentinels,bad=cleaning_expressions(features)
                con.execute(f'''CREATE TABLE cleaned AS SELECT m.*, {clean} AS clean_x,{sentinels} AS sentinels,
                    {bad} AS quality_invalid, NOT ({bad}) AND m.primary_role<>'quarantine_conflict' AS quality_eligible
                    FROM normalized n JOIN memberships m USING(source_file,parsed_row)''')
                assert con.execute('SELECT count(*),count(DISTINCT (source_file,parsed_row)) FROM cleaned').fetchone()==(split['rows'],split['rows'])
                assert con.execute('SELECT count(*) FROM (SELECT group_id FROM cleaned GROUP BY group_id HAVING count(DISTINCT (clean_x,sentinels,quality_eligible))>1)').fetchone()[0]==0
                result['quality_support']=fetch_dict(con,'''SELECT primary_role,label,binary_label,quality_invalid,quality_eligible,count(*) AS rows,count(DISTINCT group_id) AS groups FROM cleaned GROUP BY ALL ORDER BY ALL''')
                result['feature_quality']=[]
                for i,f in enumerate(features,1):
                    counts=con.execute(f'SELECT count(*) FILTER (WHERE x[{i}] IS NULL),count(*) FILTER (WHERE x[{i}]<0),count(*) FILTER (WHERE x[{i}]=-1) FROM normalized').fetchone()
                    result['feature_quality'].append({'id':f['id'],'name':f['name'],'source_missing_rows':counts[0],'negative_rows':counts[1],'minus1_rows':counts[2]})
                con.execute('DROP TABLE normalized')
                clean_path=destination/'cleaned.parquet'
                con.execute(f"COPY (SELECT * FROM cleaned ORDER BY source_file,parsed_row) TO {lit(str(clean_path))} (FORMAT PARQUET, COMPRESSION ZSTD)")
                result['cleaned']={'path':str(clean_path.resolve()),'sha256':sha(clean_path),'rows':split['rows']}
                write_json(report,result)
                for protocol in ['primary','stress']+(['cl'] if name!='cic-ids-2017' else []):
                    tick=time.perf_counter(); folder=destination/protocol; folder.mkdir()
                    print(f'{name}/{protocol}: fit permitted pilot and verify all eligible groups',flush=True)
                    params=fit_parameters(con,features,protocol)
                    params.update(dataset=name,source_split_sha256=split['manifest_sha256'],cleaned_sha256=result['cleaned']['sha256'])
                    fit_ids=folder/'fit-membership.parquet'
                    con.execute(f"COPY (SELECT source_file,parsed_row,group_id FROM fit ORDER BY group_id) TO {lit(str(fit_ids))} (FORMAT PARQUET, COMPRESSION ZSTD)")
                    params['fit_membership_sha256']=sha(fit_ids)
                    validation=verify_vectors(con,params)
                    role=ALLOWED[protocol]
                    support=fetch_dict(con,f'''SELECT {role} AS role,task_id,binary_label,label,count(*) AS rows,count(DISTINCT group_id) AS groups FROM cleaned WHERE quality_eligible GROUP BY ALL ORDER BY ALL''')
                    artifacts={}
                    for partition in ['train','validation']:
                        if partition=='train': selection='SELECT f.*,t.vector FROM fit f JOIN transformed t USING(group_id)'
                        else: selection=f"SELECT c.*,t.vector FROM cleaned c JOIN transformed t USING(group_id) WHERE c.quality_eligible AND c.{role}='validation'"
                        out=folder/(partition+'.parquet')
                        con.execute(f"COPY (SELECT source_file,parsed_row,group_id,label,binary_label,task_id,representative,vector FROM ({selection})) TO {lit(str(out))} (FORMAT PARQUET, COMPRESSION ZSTD)")
                        counts=fetch_dict(con,f'SELECT binary_label,count(*) AS rows FROM read_parquet({lit(str(out))}) GROUP BY binary_label ORDER BY binary_label')
                        assert {x['binary_label'] for x in counts}=={0,1}, 'Pilot/validation lacks binary support'
                        artifacts[partition]={'path':str(out.resolve()),'sha256':sha(out),'binary_support':counts}
                    write_json(folder/'transform.json',params)
                    write_json(ROOT/'reports/preprocessing/transforms'/f'{name}-{protocol}.json',params)
                    result['pipelines'].append({'protocol':protocol,'fit_rows':params['fit_rows'],'output_features':len(params['output_names']),
                        'fit_group_set_sha256':params['fit_group_set_sha256'],'fit_membership':str(fit_ids.resolve()),'fit_membership_sha256':sha(fit_ids),
                        'transform_path':str((folder/'transform.json').resolve()),'transform_sha256':sha(folder/'transform.json'),
                        'validation':validation,'support':support,'artifacts':artifacts,'elapsed_seconds':time.perf_counter()-tick})
                    write_json(report,result)
                    con.execute('DROP TABLE transformed'); con.execute('DROP TABLE fit')
                for f in contract['source_files']:
                    stat=Path(f['path']).stat(); assert (stat.st_size,stat.st_mtime_ns)==(f['bytes'],f['mtime_ns'])
                result['status']='COMPLETED'
            finally: con.close()
    except Exception as exc:
        result.update(status='FAILED',error=repr(exc)); raise
    finally:
        done.set(); thread.join(timeout=2)
        result.update(elapsed_seconds=time.perf_counter()-began,sampled_peak_process_rss_bytes=peak[0])
        write_json(report,result)
    print(f'{name}: COMPLETED',flush=True)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--family',action='append'); args=p.parse_args()
    for name in args.family or ['cic-ids-2017','ND-UNSW-NB15-v3']: family(name)


if __name__=='__main__': main()
