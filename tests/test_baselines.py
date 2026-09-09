import sys
import unittest
import warnings
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from baseline_metrics import evaluate,threshold_for_fpr
from run_baseline_pilot import make_model,load_partition


class BaselineTests(unittest.TestCase):
    def test_confusion_and_absent_family(self):
        r=evaluate([0,0,1,1],[0.1,0.9,0.8,0.2],['benign','benign','a','b'],['benign','a','b','absent'])
        self.assertEqual(r['confusion'],{'tn':1,'fp':1,'fn':1,'tp':1})
        self.assertEqual(r['binary_macro_f1'],0.5); self.assertEqual(r['benign_fpr'],0.5)
        self.assertEqual(r['attack_family_recall']['a']['binary_attack_recall'],1)
        self.assertIsNone(r['attack_family_recall']['absent']['binary_attack_recall'])

    def test_ties_do_not_exceed_false_positive_budget(self):
        y=np.array([0]*100+[1]*3); p=np.array([0.9]*3+[0.1]*97+[0.95,0.9,0.2])
        t=threshold_for_fpr(y,p)
        self.assertGreater(t,0.9); self.assertLessEqual(int(((p>=t)&(y==0)).sum()),1)
        self.assertGreater(threshold_for_fpr([0,1],[1.,1.],0),1)
        self.assertIsNone(threshold_for_fpr([1],[0.5]))

    def test_invalid_probability_and_sealed_access_rejected(self):
        with self.assertRaises(ValueError): threshold_for_fpr([0,1],[0.1,float('nan')])
        with self.assertRaises(ValueError): load_partition('cic-ids-2017','primary','sealed_test',{},156)

    def test_float32_can_merge_float64_inputs(self):
        x=np.array([1.0,np.nextafter(1.0,2.0)],dtype=np.float64)
        self.assertEqual(len(np.unique(x)),2); self.assertEqual(len(np.unique(x.astype(np.float32))),1)

    def test_all_estimators_fit_and_emit_finite_binary_probabilities(self):
        rng=np.random.default_rng(17); x=rng.normal(size=(80,6)); y=(x[:,0]>0).astype(int)
        with threadpool_limits(limits=2),warnings.catch_warnings():
            warnings.simplefilter('ignore')
            for kind in ['prior','logistic','extra_trees','mlp']:
                model=make_model(kind); model.fit(x,y); p=model.predict_proba(x)
                self.assertTrue(np.isfinite(p).all()); self.assertTrue(np.allclose(p.sum(axis=1),1))
                self.assertEqual(list(model.classes_),[0,1])


if __name__=='__main__': unittest.main()
