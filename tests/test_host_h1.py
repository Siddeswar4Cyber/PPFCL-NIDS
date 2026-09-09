import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from host_feasibility_h1 import component_map,support_acceptance,side


class HostTests(unittest.TestCase):
    def test_shared_endpoint_and_feature_group_bridges(self):
        addresses=['a','b','c','d','e']; edges=[('a','b'),('b','c'),('d','e')]
        initial=component_map(addresses,edges)
        self.assertEqual(initial['a'],initial['c']); self.assertNotEqual(initial['a'],initial['d'])
        bridged=component_map(addresses,edges,[['a','d']])
        self.assertEqual(len(set(bridged.values())),1)
        self.assertEqual(bridged,component_map(list(reversed(addresses)),list(reversed(edges)),[['d','a']]))

    def test_one_class_or_overlap_is_not_accepted(self):
        good=[{'partition':p,'rows':1000,'benign':900,'attack':100} for p in ['train','validation']]
        self.assertEqual(support_acceptance(good,0,0,0),[])
        self.assertTrue(support_acceptance(good,1,0,0))
        good[1].update(attack=0,benign=1000)
        self.assertIn('validation: fewer than 20 attack rows',support_acceptance(good,0,0,0))


if __name__=='__main__': unittest.main()
