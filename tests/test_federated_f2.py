import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import torch
from neural_runtime import network
import federated_f1 as f1
import federated_f2 as f2


class F2Tests(unittest.TestCase):
    def test_proximal_gradient_includes_bias(self):
        model=network(3,dtype=torch.float64); anchor=f1.state_copy(model)
        with torch.no_grad():
            for p in model.parameters(): p.add_(.125)
        x=torch.tensor([[.1,.2,.3],[.2,-.1,.4]],dtype=torch.float64); y=torch.tensor([0.,1.],dtype=torch.float64)
        f1.objective(model,x,y).backward(); base={k:p.grad.clone() for k,p in model.named_parameters()}
        model.zero_grad(); f2.proximal_objective(model,x,y,anchor,.01).backward()
        for k,p in model.named_parameters():
            torch.testing.assert_close(p.grad-base[k],.01*(p.detach()-anchor[k]),rtol=1e-10,atol=1e-14)
        self.assertTrue(all(not v.requires_grad for v in anchor.values()))

    def test_zero_mu_and_seed17_match_f1(self):
        torch.set_num_threads(2)
        x=torch.linspace(-1,1,771).reshape(257,3); y=(x[:,0]>0).float(); start=f1.state_copy(network(3))
        before=f1.state_digest(start)
        order=f2.epoch_order(257,'d','primary','iid',2,3,17)
        np.testing.assert_array_equal(order,f1.epoch_order(257,'d','primary','iid',2,3))
        self.assertFalse(np.array_equal(order,f2.epoch_order(257,'d','primary','iid',2,3,29)))
        a,wa=f1.update(start,x,y,.001,order); b,wb=f2.update(start,x,y,.001,order,0)
        self.assertEqual(wa,wb); self.assertEqual(f1.state_digest(a),f1.state_digest(b))
        f2.update(start,x,y,.001,order,.1)
        self.assertEqual(before,f1.state_digest(start))

    def test_server_numpy_recurrence_persistence_and_sign(self):
        start={'weight':torch.tensor([1.,-2.]),'bias':torch.tensor([.5])}
        expected={k:v.numpy().copy() for k,v in start.items()}; m={k:np.zeros(v.shape) for k,v in expected.items()}
        v={k:np.full(x.shape,1e-6) for k,x in expected.items()}; moments=None
        for step in range(3):
            averaged={k:(x+(.01 if step!=1 else -.003)) for k,x in start.items()}
            start_hash=f1.state_digest(start)
            for k in start:
                delta=averaged[k].numpy().astype('float64')-expected[k].astype('float64')
                m[k]=.9*m[k]+(1-.9)*delta; v[k]=.99*v[k]+(1-.99)*delta**2
                expected[k]=(expected[k].astype('float64')+.01*m[k]/(np.sqrt(v[k])+.001)).astype('float32')
            out,after,before=f2.server_adam(start,averaged,moments,.01)
            self.assertEqual(start_hash,f1.state_digest(start))
            for k in start:
                np.testing.assert_array_equal(out[k].numpy(),expected[k])
                np.testing.assert_allclose(after['m'][k].numpy(),m[k],rtol=0,atol=1e-16)
                np.testing.assert_allclose(after['v'][k].numpy(),v[k],rtol=0,atol=1e-16)
                if step==0: self.assertTrue(torch.all(out[k]>start[k]))
            start=out; moments=after

    def test_invalid_server_and_proximal_parameters(self):
        start={'w':torch.tensor([1.])}
        for lr in [0,-1,float('nan')]:
            with self.assertRaises(ValueError): f2.server_adam(start,start,None,lr)
        with self.assertRaises(ValueError): f2.server_adam(start,{'x':torch.tensor([1.])},None,.1)
        with self.assertRaises(ValueError): f2.server_adam(start,{'w':torch.tensor([float('inf')])},None,.1)
        with self.assertRaises(ValueError): f2.update(start,None,None,.001,None,-.1)


if __name__=='__main__': unittest.main()
