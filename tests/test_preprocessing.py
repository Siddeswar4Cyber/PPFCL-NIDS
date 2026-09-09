import json
import sys
import unittest
from pathlib import Path
import duckdb
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from preprocess_p1 import cleaning_expressions, fit_parameters, vector_sql, verify_vectors


class PreprocessingTests(unittest.TestCase):
    def connection(self):
        c=duckdb.connect(); self.addCleanup(c.close)
        c.execute('''CREATE TABLE cleaned(source_file INT,parsed_row BIGINT,group_id VARCHAR,label VARCHAR,binary_label INT,
            primary_role VARCHAR,stress_role VARCHAR,task_role VARCHAR,task_id INT,representative BOOLEAN,
            clean_x DOUBLE[],sentinels DOUBLE[],quality_eligible BOOLEAN)''')
        return c

    def add(self,c,i,value,role='development_train',task=1,valid=True):
        c.execute('INSERT INTO cleaned VALUES (0,?,?,?,?,?,?,?,?,true,?,[],?)',[i,str(i),'benign' if i%2 else 'attack',0 if i%2 else 1,role,role,role,task,[value],valid])

    def test_forbidden_roles_and_future_tasks_do_not_change_fit(self):
        c=self.connection(); features=[{'id':'c000','name':'rate'}]
        self.add(c,1,2); self.add(c,2,4)
        for i,role in enumerate(['validation','sealed_test','private_train','public_reference'],3): self.add(c,i,10000,role)
        self.add(c,7,999,'development_train',task=2)
        self.add(c,8,99999,valid=False)
        before=fit_parameters(c,features,'cl')
        self.assertEqual(before['fit_rows'],2); self.assertEqual(before['parameters'][0]['median'],3)
        self.assertEqual(before['parameters'][0]['scale'],4)
        c.execute("UPDATE cleaned SET clean_x=[1e100] WHERE group_id NOT IN ('1','2')")
        after=fit_parameters(c,features,'cl')
        self.assertEqual(before,after)

    def test_missing_sentinel_and_negative_policy(self):
        c=self.connection(); features=[{'id':'c000','name':'rate'},{'id':'c001','name':'Init_Win_bytes_forward'}]
        clean,sentinel,bad=cleaning_expressions(features)
        rows=c.execute(f'SELECT {clean},{sentinel},{bad} FROM (VALUES ([2.0,-1.0]),([NULL,3.0]),([-2.0,3.0]),([2.0,-2.0])) t(x)').fetchall()
        self.assertEqual(rows[0],([2.0,None],[1.0],False))
        self.assertEqual(rows[1],([None,3.0],[0.0],False))
        self.assertTrue(rows[2][2]); self.assertTrue(rows[3][2])

    def test_saved_transform_preserves_missing_distinction_and_future_range(self):
        c=self.connection(); features=[{'id':'c000','name':'rate'}]
        self.add(c,1,2); self.add(c,2,4); self.add(c,3,None,'validation'); self.add(c,4,3,'sealed_test'); self.add(c,5,1000,'private_train')
        params=fit_parameters(c,features,'primary')
        restored=json.loads(json.dumps(params))
        self.assertEqual(vector_sql(params),vector_sql(restored))
        checks=verify_vectors(c,restored)
        self.assertEqual(checks['merged_S1_groups'],0)
        vectors=dict(c.execute('SELECT group_id,vector FROM transformed').fetchall())
        self.assertEqual(vectors['3'],[0.75,1.0]); self.assertEqual(vectors['4'],[0.75,0.0]); self.assertEqual(vectors['5'],[250.0,0.0])

    def test_all_missing_column_has_explicit_fixed_fallback(self):
        c=self.connection(); self.add(c,1,None); self.add(c,2,7,'validation')
        params=fit_parameters(c,[{'id':'c000','name':'rate'}],'primary')
        self.assertTrue(params['parameters'][0]['all_missing_fallback'])
        self.assertEqual(params['parameters'][0]['median'],0)
        self.assertEqual(verify_vectors(c,params)['finite_shape_failures'],0)


if __name__=='__main__': unittest.main()
