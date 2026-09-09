"""Pre-score CIC precision amendment: exclude merged groups, refit all candidates."""
import json
import tempfile
import time
from pathlib import Path
import duckdb
from audit_datasets import lit,write_json,fetch_dict
from preprocess_p1 import sha,fit_parameters,vector_sql,verify_vectors

ROOT=Path(__file__).resolve().parents[1]


def main():
    began=time.perf_counter(); name='cic-ids-2017'; destination=ROOT/'data/processed/P2'/name
    if destination.exists(): raise RuntimeError('P2 output already exists; refusing overwrite')
    original=json.loads((ROOT/'reports/preprocessing'/f'{name}.json').read_text())
    assert original['status']=='COMPLETED' and sha(original['cleaned']['path'])==original['cleaned']['sha256']
    features=json.loads((ROOT/'reports/splits/contracts'/f'{name}.json').read_text())['predictors']
    destination.mkdir(parents=True)
    result={'version':'P2','dataset':name,'status':'RUNNING','source_P1_cleaned_sha256':original['cleaned']['sha256'],'script_sha256':sha(__file__),'pipelines':[]}
    output=ROOT/'reports/preprocessing/cic-ids-2017-P2.json'
    try:
        with tempfile.TemporaryDirectory(prefix='ppfcl-p2-') as temp:
            con=duckdb.connect(str(Path(temp)/'work.duckdb'))
            try:
                con.execute("SET memory_limit='4GB'"); con.execute('SET threads=8')
                con.execute(f"CREATE VIEW original AS SELECT * FROM read_parquet({lit(original['cleaned']['path'])})")
                con.execute('CREATE TABLE excluded(group_id VARCHAR)')
                for pipe in original['pipelines']:
                    params=json.loads(Path(pipe['transform_path']).read_text())
                    assert sha(pipe['transform_path'])==pipe['transform_sha256']
                    print(f'P2: collect {pipe["protocol"]} float32 collision groups',flush=True)
                    con.execute(f"CREATE TABLE projected AS SELECT group_id,list_transform({vector_sql(params)},v->cast(v AS FLOAT)) AS vector FROM original WHERE quality_eligible AND representative")
                    con.execute('INSERT INTO excluded SELECT group_id FROM projected JOIN (SELECT vector FROM projected GROUP BY vector HAVING count(*)>1) b USING(vector)')
                    con.execute('DROP TABLE projected')
                con.execute('CREATE TABLE exclusions AS SELECT DISTINCT group_id FROM excluded')
                result['excluded_groups']=con.execute('SELECT count(*) FROM exclusions').fetchone()[0]
                con.execute('''CREATE TABLE cleaned AS SELECT o.* EXCLUDE(quality_eligible),o.quality_eligible AS P1_eligible,
                    e.group_id IS NOT NULL AS precision_invalid,o.quality_eligible AND e.group_id IS NULL AS quality_eligible
                    FROM original o LEFT JOIN exclusions e USING(group_id)''')
                result['exclusion_support']=fetch_dict(con,'SELECT primary_role,label,binary_label,count(*) AS rows,count(DISTINCT group_id) AS groups FROM cleaned WHERE precision_invalid GROUP BY ALL ORDER BY ALL')
                path=destination/'cleaned.parquet'; ids=destination/'precision-exclusions.parquet'
                con.execute(f"COPY (SELECT * FROM cleaned ORDER BY source_file,parsed_row) TO {lit(str(path))} (FORMAT PARQUET, COMPRESSION ZSTD)")
                con.execute(f"COPY (SELECT * FROM exclusions ORDER BY group_id) TO {lit(str(ids))} (FORMAT PARQUET, COMPRESSION ZSTD)")
                result['cleaned']={'path':str(path.resolve()),'sha256':sha(path),'rows':con.execute('SELECT count(*) FROM cleaned').fetchone()[0]}
                result['exclusions']={'path':str(ids.resolve()),'sha256':sha(ids)}
                assert result['cleaned']['rows']==original['cleaned']['rows']
                for protocol in ['primary','stress']:
                    print(f'P2/{protocol}: refit and verify precision',flush=True)
                    folder=destination/protocol; folder.mkdir(); params=fit_parameters(con,features,protocol)
                    params.update(version='P2',dataset=name,cleaned_sha256=result['cleaned']['sha256'],source_split_sha256=original['source_manifest_sha256'])
                    checks=verify_vectors(con,params)
                    bad=con.execute('SELECT count(*) FROM transformed WHERE NOT list_bool_and(list_transform(vector,v->isfinite(cast(v AS FLOAT))))').fetchone()[0]
                    merges=con.execute('SELECT count(*) FROM (SELECT list_transform(vector,v->cast(v AS FLOAT)) AS z FROM transformed GROUP BY z HAVING count(*)>1)').fetchone()[0]
                    assert bad==0 and merges==0, 'P2 float32 gate failed; no training authorized'
                    fitids=folder/'fit-membership.parquet'
                    con.execute(f"COPY (SELECT source_file,parsed_row,group_id FROM fit ORDER BY group_id) TO {lit(str(fitids))} (FORMAT PARQUET, COMPRESSION ZSTD)")
                    params['fit_membership_sha256']=sha(fitids)
                    artifacts={}
                    for partition in ['train','validation']:
                        selection='SELECT f.*,t.vector FROM fit f JOIN transformed t USING(group_id)' if partition=='train' else f"SELECT c.*,t.vector FROM cleaned c JOIN transformed t USING(group_id) WHERE c.quality_eligible AND c.{protocol}_role='validation'"
                        out=folder/(partition+'.parquet')
                        con.execute(f"COPY (SELECT source_file,parsed_row,group_id,label,binary_label,task_id,representative,vector FROM ({selection})) TO {lit(str(out))} (FORMAT PARQUET, COMPRESSION ZSTD)")
                        counts=fetch_dict(con,f'SELECT binary_label,count(*) AS rows FROM read_parquet({lit(str(out))}) GROUP BY binary_label ORDER BY binary_label')
                        assert {x['binary_label'] for x in counts}=={0,1}
                        artifacts[partition]={'path':str(out.resolve()),'sha256':sha(out),'binary_support':counts}
                    write_json(folder/'transform.json',params)
                    write_json(ROOT/'reports/preprocessing/transforms'/f'{name}-{protocol}-P2.json',params)
                    support=fetch_dict(con,f'SELECT {protocol}_role AS role,label,binary_label,count(*) AS rows,count(DISTINCT group_id) AS groups FROM cleaned WHERE quality_eligible GROUP BY ALL ORDER BY ALL')
                    result['pipelines'].append({'protocol':protocol,'fit_rows':params['fit_rows'],'fit_group_set_sha256':params['fit_group_set_sha256'],
                        'fit_membership':str(fitids.resolve()),'fit_membership_sha256':sha(fitids),'output_features':len(params['output_names']),
                        'transform_path':str((folder/'transform.json').resolve()),'transform_sha256':sha(folder/'transform.json'),'artifacts':artifacts,'support':support,
                        'validation':checks,'float32_gate':{'status':'PASSED','nonfinite_vectors':bad,'merged_vectors':merges}})
                    write_json(output,result); con.execute('DROP TABLE fit'); con.execute('DROP TABLE transformed')
                result['status']='COMPLETED'
            finally: con.close()
    except Exception as exc:
        result.update(status='FAILED',error=repr(exc)); raise
    finally:
        result['elapsed_seconds']=time.perf_counter()-began; write_json(output,result)
    print('P2 complete; all CIC candidates must use this population',flush=True)


if __name__=='__main__': main()
