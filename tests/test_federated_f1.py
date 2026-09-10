import sys
import unittest
from pathlib import Path
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from federated_f1 import aggregate, objective, epoch_order, update, state_copy
from neural_runtime import network


class FederatedTests(unittest.TestCase):
    def test_unequal_weights_and_biases(self):
        a={'weight':torch.tensor([1.,3.]),'bias':torch.tensor([-1.])}
        b={'weight':torch.tensor([9.,7.]),'bias':torch.tensor([3.])}
        out=aggregate([a,b],[1,3])
        torch.testing.assert_close(out['weight'],torch.tensor([7.,6.]),rtol=0,atol=0)
        torch.testing.assert_close(out['bias'],torch.tensor([2.]),rtol=0,atol=0)
        self.assertEqual(a['weight'][0].item(),1.)

    def test_invalid_uploads_rejected(self):
        a={'w':torch.ones(2)}
        for states,counts in [([a,a],[1,0]),([a,{'w':torch.ones(3)}],[1,1]),
                              ([a,{'w':torch.tensor([float('nan'),1.])}],[1,1]),([a,{'b':torch.ones(2)}],[1,1])]:
            with self.assertRaises(ValueError): aggregate(states,counts)

    def test_regularizer_is_independent_of_short_batch(self):
        model=network(2,dtype=torch.float64); x=torch.ones((3,2),dtype=torch.float64); y=torch.zeros(3,dtype=torch.float64)
        full=objective(model,x,y)
        one=objective(model,x[:1],y[:1])
        self.assertAlmostEqual(full.item(),one.item(),places=12)
        p=list(model.parameters()); regularizer=full-torch.nn.functional.binary_cross_entropy_with_logits(model(x).squeeze(1),y)
        grads=torch.autograd.grad(regularizer,p)
        for name,param,g in zip([n for n,_ in model.named_parameters()],p,grads):
            expected=param.detach()*(.0001/256) if name.endswith('weight') else torch.zeros_like(param)
            torch.testing.assert_close(g,expected,atol=1e-12,rtol=1e-10)

    def test_single_client_matches_local_and_preserves_start(self):
        torch.set_num_threads(2); x=torch.arange(14,dtype=torch.float32).reshape(7,2)/10; y=torch.tensor([0.,1.,0.,1.,1.,0.,1.])
        start=state_copy(network(2)); original={k:v.clone() for k,v in start.items()}
        local=start; global_state=start
        for epoch in [1,2]:
            order=epoch_order(7,'fixture','primary','iid',epoch,0)
            local,a=update(local,x,y,.001,order)
            uploaded,b=update(global_state,x,y,.001,order)
            global_state=aggregate([uploaded],[7])
            self.assertEqual(a,b)
            self.assertTrue(all(torch.equal(local[k],global_state[k]) for k in local))
        self.assertTrue(all(torch.equal(start[k],original[k]) for k in start))


if __name__=='__main__': unittest.main()
