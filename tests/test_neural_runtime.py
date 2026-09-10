"""N1 loss/gradient/update checks against independent NumPy formulas."""
import sys
import unittest
from pathlib import Path
import numpy as np
import torch
from scipy.special import expit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from neural_runtime import network, objective, optimizer
from neural_migration import to_torch
from test_neural_migration import fixture


def oracle(weights, biases, x, y, alpha):
    a = [x]; pre = []
    for i in range(3):
        z = a[-1] @ weights[i].T + biases[i]
        pre.append(z); a.append(np.maximum(z, 0) if i < 2 else z)
    logits = a[-1][:, 0]
    loss = np.mean(np.logaddexp(0, logits)-y*logits)+.5*alpha/len(y)*sum((w*w).sum() for w in weights)
    delta = (expit(logits)-y)[:, None]/len(y); grads = [None]*6
    for i in reversed(range(3)):
        grads[2*i] = delta.T @ a[i]+alpha/len(y)*weights[i]
        grads[2*i+1] = delta.sum(axis=0)
        if i: delta = (delta @ weights[i])*(pre[i-1] > 0)
    return loss, grads


class RuntimeTests(unittest.TestCase):
    def test_native_adam_three_steps_and_partial_batch(self):
        torch.set_num_threads(2)
        model = network(3, dtype=torch.float64, seed=29)
        params = list(model.parameters()); reference = [p.detach().numpy().copy() for p in params]
        m = [np.zeros_like(p) for p in reference]; v = [np.zeros_like(p) for p in reference]
        opt = optimizer(model, .0003); rng = np.random.default_rng(43)
        x = rng.normal(size=(10, 3)); y = np.array([0,1,1,0,1,0,1,0,0,1], dtype=float)
        for step, (start, end) in enumerate([(0,4),(4,8),(8,10)], 1):
            expected_loss, gradients = oracle(reference[::2], reference[1::2], x[start:end], y[start:end], .0001)
            opt.zero_grad(set_to_none=True)
            loss = objective(model, torch.tensor(x[start:end]), torch.tensor(y[start:end]))
            loss.backward()
            self.assertAlmostEqual(loss.item(), expected_loss, places=12)
            for p, g in zip(params, gradients):
                np.testing.assert_allclose(p.grad.numpy(), g, atol=1e-11, rtol=1e-10)
            for i, g in enumerate(gradients):
                m[i] = .9*m[i]+.1*g; v[i] = .999*v[i]+.001*g*g
                reference[i] -= .0003*(m[i]/(1-.9**step))/(np.sqrt(v[i]/(1-.999**step))+1e-8)
            opt.step()
            for p, expected in zip(params, reference):
                np.testing.assert_allclose(p.detach().numpy(), expected, atol=1e-11, rtol=1e-10)

    def test_bce_extreme_logits_remains_finite(self):
        z = torch.tensor([-1000., 1000., -1000., 1000.], dtype=torch.float64, requires_grad=True)
        y = torch.tensor([0., 1., 1., 0.], dtype=torch.float64)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(z, y)
        loss.backward()
        self.assertEqual(loss.item(), 500.)
        np.testing.assert_array_equal(z.grad.numpy(), [0., 0., -.25, .25])

    def test_converter_uses_transpose_biases_and_logits(self):
        model = to_torch(fixture())
        x = torch.tensor([[0., 0.], [1., 1.], [-3., 2.]], dtype=torch.float64)
        np.testing.assert_array_equal(model(x).detach().numpy()[:, 0], [-1.25, -7.25, -.25])


if __name__ == '__main__': unittest.main()
