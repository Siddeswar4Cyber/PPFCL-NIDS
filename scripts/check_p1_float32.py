"""Gate sklearn tree input precision before reading any model performance."""
import json
import tempfile
from pathlib import Path
import duckdb
from audit_datasets import lit, write_json
from preprocess_p1 import vector_sql, sha

ROOT=Path(__file__).resolve().parents[1]


def main():
    for name in ['cic-ids-2017','ND-UNSW-NB15-v3']:
        r=json.loads((ROOT/'reports/preprocessing'/f'{name}.json').read_text())
        assert r['status']=='COMPLETED' and sha(r['cleaned']['path'])==r['cleaned']['sha256']
        results=[]
        with tempfile.TemporaryDirectory(prefix='ppfcl-precision-') as temp:
            con=duckdb.connect(str(Path(temp)/'work.duckdb'))
            try:
                con.execute("SET memory_limit='4GB'"); con.execute('SET threads=8')
                con.execute(f"CREATE VIEW cleaned AS SELECT * FROM read_parquet({lit(r['cleaned']['path'])})")
                for pipe in r['pipelines']:
                    if pipe['protocol']=='cl': continue
                    print(f'{name}/{pipe["protocol"]}: check FLOAT32 input equality',flush=True)
                    params=json.loads(Path(pipe['transform_path']).read_text()); assert sha(pipe['transform_path'])==pipe['transform_sha256']
                    con.execute(f'''CREATE TABLE projected AS SELECT group_id,primary_role,
                        list_transform({vector_sql(params)},v -> cast(v AS FLOAT)) AS vector
                        FROM cleaned WHERE quality_eligible AND representative''')
                    finite=con.execute('SELECT count(*) FROM projected WHERE NOT list_bool_and(list_transform(vector,v -> isfinite(v)))').fetchone()[0]
                    collisions=con.execute('''SELECT count(*),coalesce(sum(groups),0),coalesce(sum(roles>1),0) FROM
                        (SELECT count(*) AS groups,count(DISTINCT primary_role) AS roles FROM projected GROUP BY vector HAVING count(*)>1)''').fetchone()
                    result={'dataset':name,'protocol':pipe['protocol'],'dtype':'float32','nonfinite_vectors':finite,'merged_vectors':collisions[0],
                            'groups_in_merged_vectors':collisions[1],'cross_role_vectors':collisions[2],
                            'status':'PASSED' if finite==0 and collisions[0]==0 else 'REJECTED_FOR_P1_TREE_INPUT',
                            'cleaned_sha256':r['cleaned']['sha256'],'transform_sha256':pipe['transform_sha256']}
                    results.append(result); print(json.dumps(result),flush=True)
                    con.execute('DROP TABLE projected')
                    write_json(ROOT/'reports/baselines/precision'/f'{name}.json',results)
            finally: con.close()


if __name__=='__main__': main()
