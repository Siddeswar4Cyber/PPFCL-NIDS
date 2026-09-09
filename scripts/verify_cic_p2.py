"""Verify the saved precision amendment before any CIC model fit."""
import json
from pathlib import Path
import duckdb
from audit_datasets import lit,write_json
from preprocess_p1 import sha,fit_parameters,vector_sql

ROOT=Path(__file__).resolve().parents[1]


def main():
    r=json.loads((ROOT/'reports/preprocessing/cic-ids-2017-P2.json').read_text())
    old=json.loads((ROOT/'reports/preprocessing/cic-ids-2017.json').read_text())
    assert r['status']=='COMPLETED' and sha(r['cleaned']['path'])==r['cleaned']['sha256']
    assert sha(old['cleaned']['path'])==r['source_P1_cleaned_sha256']
    assert sha(r['exclusions']['path'])==r['exclusions']['sha256']
    features=json.loads((ROOT/'reports/splits/contracts/cic-ids-2017.json').read_text())['predictors']
    con=duckdb.connect(); con.execute("SET memory_limit='4GB'"); con.execute('SET threads=8')
    try:
        con.execute(f"CREATE VIEW cleaned AS SELECT * FROM read_parquet({lit(r['cleaned']['path'])})")
        con.execute(f"CREATE VIEW old AS SELECT * FROM read_parquet({lit(old['cleaned']['path'])})")
        assert con.execute('SELECT count(*),count(DISTINCT (source_file,parsed_row)) FROM cleaned').fetchone()==(r['cleaned']['rows'],r['cleaned']['rows'])
        joined=con.execute('''SELECT count(*),count(*) FILTER (WHERE c.group_id<>o.group_id OR c.primary_role<>o.primary_role OR c.stress_role<>o.stress_role
            OR c.label<>o.label OR c.binary_label<>o.binary_label OR c.clean_x IS DISTINCT FROM o.clean_x OR c.sentinels IS DISTINCT FROM o.sentinels
            OR c.quality_eligible<>(o.quality_eligible AND NOT c.precision_invalid))
            FROM cleaned c JOIN old o USING(source_file,parsed_row)''').fetchone()
        assert joined==(r['cleaned']['rows'],0)
        for p in r['pipelines']:
            assert sha(p['transform_path'])==p['transform_sha256'] and sha(p['fit_membership'])==p['fit_membership_sha256']
            saved=json.loads(Path(p['transform_path']).read_text()); fresh=fit_parameters(con,features,p['protocol'])
            assert fresh['parameters']==saved['parameters'] and fresh['fit_group_set_sha256']==saved['fit_group_set_sha256']
            for partition,artifact in p['artifacts'].items():
                assert sha(artifact['path'])==artifact['sha256']
                con.execute(f"CREATE OR REPLACE VIEW output AS SELECT * FROM read_parquet({lit(artifact['path'])})")
                if partition=='train': con.execute('CREATE OR REPLACE VIEW permitted AS SELECT * FROM fit')
                else: con.execute(f"CREATE OR REPLACE VIEW permitted AS SELECT * FROM cleaned WHERE quality_eligible AND {p['protocol']}_role='validation'")
                expected=con.execute('SELECT count(*) FROM permitted').fetchone()[0]
                assert con.execute('SELECT count(*),count(DISTINCT (source_file,parsed_row)) FROM output').fetchone()==(expected,expected)
                assert con.execute(f'SELECT count(*),count(*) FILTER (WHERE o.vector IS DISTINCT FROM {vector_sql(saved)} OR o.label<>c.label) FROM output o JOIN permitted c USING(source_file,parsed_row,group_id)').fetchone()==(expected,0)
            for role in ['development_train','validation','sealed_test','private_train','public_reference']:
                assert {s['binary_label'] for s in p['support'] if s['role']==role and s['groups']>0}=={0,1}
            assert p['float32_gate']['status']=='PASSED'
    finally: con.close()
    write_json(ROOT/'reports/preprocessing/P2-verification.json',{'status':'PASSED','source_roles_unchanged':True,'parameters_refitted_on_new_permitted_samples':True,'model_ready_vectors_reproduced':True,'both_binary_classes_in_every_role':True,'excluded_groups':r['excluded_groups'],'excluded_rows':sum(x['rows'] for x in r['exclusion_support'])})
    print('P2 persisted verification PASSED')


if __name__=='__main__': main()
