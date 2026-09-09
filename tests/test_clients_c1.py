import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_clients_c1 import group_uniform,assign,choose,acceptable,binary_support


class ClientTests(unittest.TestCase):
    def test_duplicate_groups_keep_owner_and_input_order_does_not_matter(self):
        groups=np.array(['a','b','a','c']); labels=np.array(['attack','benign','attack','benign'])
        p={'attack':[.1,.2,.3,.1,.3]}; u=group_uniform(groups,'scope'); owners=assign(u,labels,p)
        self.assertEqual(owners[0],owners[2])
        order=np.array([3,1,0,2]); np.testing.assert_array_equal(assign(group_uniform(groups[order],'scope'),labels[order],p),owners[order])

    def test_unknown_validation_label_uses_fixed_uniform(self):
        u=np.array([0.,.21,.41,.61,.99]); labels=np.array(['unknown']*5)
        np.testing.assert_array_equal(assign(u,labels,{}),np.arange(5))
        with self.assertRaises(ValueError): assign(u,labels,{'unknown':[1,1,1,1,1]})

    def test_failed_attempts_preserved_without_relaxing_floors(self):
        groups=np.array([str(i) for i in range(50)]); labels=np.array(['benign']*50); y=np.zeros(50,dtype=int)
        owners,p,attempts=choose(groups,labels,y,'tiny',.1)
        self.assertIsNone(owners); self.assertIsNone(p); self.assertEqual(len(attempts),21)
        self.assertEqual(attempts[-1]['method'],'dirichlet_uniform10_fallback')
        self.assertTrue(all(not a['accepted'] for a in attempts))

    def test_iid_training_acceptance_is_deterministic(self):
        groups=np.array([str(i) for i in range(20000)]); y=np.arange(20000)%2; labels=np.where(y==0,'benign','attack')
        a,p,attempts=choose(groups,labels,y,'valid',None); b,_,_=choose(groups,labels,y,'valid',None)
        np.testing.assert_array_equal(a,b); self.assertTrue(acceptable(binary_support(a,y))); self.assertEqual(len(attempts),1)


if __name__=='__main__': unittest.main()
