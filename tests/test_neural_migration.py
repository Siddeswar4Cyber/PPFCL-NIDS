"""Independent arithmetic fixtures for prediction-layout migration."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from neural_migration import numpy_predict, validate_model


def fixture():
    w = [np.zeros((2, 64)), np.zeros((64, 32)), np.zeros((32, 1))]
    b = [np.zeros(64), np.zeros(32), np.array([-.25])]
    w[0][:, 0] = [2, -1]
    b[0][0] = .5
    w[1][0, 0] = 3
    b[1][0] = -1
    w[2][0, 0] = -2
    return SimpleNamespace(hidden_layer_sizes=(64, 32), activation='relu', out_activation_='logistic',
                           classes_=np.array([0, 1]), n_features_in_=2, coefs_=w, intercepts_=b)


class MigrationTests(unittest.TestCase):
    def test_orientation_bias_relu_and_final_partial_batch(self):
        x = np.array([[0., 0.], [1., 1.], [-3., 2.], [0., 2.], [2., 0.]])
        logits = np.array([-1.25, -7.25, -.25, -.25, -25.25])
        expected = 1/(1+np.exp(-logits))
        np.testing.assert_allclose(numpy_predict(fixture(), x, batch_size=2), expected, atol=1e-15, rtol=0)

    def test_invalid_order_and_nonfinite_rejected(self):
        m = fixture(); m.classes_ = np.array([1, 0])
        with self.assertRaises(ValueError): validate_model(m)
        m = fixture(); m.coefs_[0][0, 0] = np.nan
        with self.assertRaises(ValueError): validate_model(m)
        with self.assertRaises(ValueError): numpy_predict(fixture(), np.array([[np.inf, 0.]]))

    def test_invalid_dimensions_rejected(self):
        with self.assertRaises(ValueError): numpy_predict(fixture(), np.zeros((2, 3)))
        with self.assertRaises(ValueError): numpy_predict(fixture(), np.zeros((2, 2)), batch_size=0)


if __name__ == '__main__': unittest.main()
