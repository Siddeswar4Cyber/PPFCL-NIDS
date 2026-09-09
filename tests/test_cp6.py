import sys
import unittest
from pathlib import Path
import duckdb
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cp6_features import transform, field_columns, overlap_gate
from run_cp6 import select_representation


class CP6Tests(unittest.TestCase):
    def test_selection_requires_macro_gain_and_ap_guard(self):
        def run(name,f1,ap,width=10):
            return {'representation':name,'input_features':width,'metrics_05':{'binary_macro_f1':f1,'average_precision':ap}}
        full=run('full',.90,.95)
        self.assertIs(select_representation([full,run('small_gain',.901,.96)]),full)
        self.assertIs(select_representation([full,run('ap_loss',.92,.94)]),full)
        better=run('qualified',.91,.95)
        self.assertIs(select_representation([full,better]),better)

    def test_augmentation_preserves_unknown_and_missing_values(self):
        x=np.array([[1.,0.],[2.,0.],[1.,1.],[9.,0.]])
        d={'columns':[0,1],'categories':[{'column':0,'missing_column':1,'value':1.}],'output_width':3}
        z=transform(x,d)
        np.testing.assert_array_equal(z[:,:2],x)
        np.testing.assert_array_equal(z[:,2],[1.,0.,0.,0.])

    def test_complete_field_groups_and_unknown_name(self):
        p={'parameters':[{'input_id':'c000','name':'a'},{'input_id':'c001','name':'b'}],
           'output_names':['c000_scaled','c001_scaled','c000_missing','c001_missing','c001_sentinel_minus1']}
        self.assertEqual(field_columns(p,['b']),[1,3,4])
        with self.assertRaises(ValueError): field_columns(p,['absent'])

    def test_reduction_rejects_cross_role_merge(self):
        with duckdb.connect() as c:
            c.execute("CREATE TABLE projected(group_id VARCHAR,primary_role VARCHAR,stress_role VARCHAR,vector DOUBLE[])")
            c.execute("INSERT INTO projected VALUES ('a','development_train','development_train',[1,2]),('b','sealed_test','sealed_test',[1,3])")
            self.assertEqual(overlap_gate(c,[0,1],'float64')['status'],'PASSED')
            r=overlap_gate(c,[0],'float32')
            self.assertEqual(r['status'],'REJECTED_UNDER_S1')
            self.assertEqual(r['cross_primary_role_vectors'],1)
            self.assertEqual(r['implicated_groups'],2)


if __name__=='__main__': unittest.main()
