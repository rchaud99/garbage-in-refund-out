import numpy as np
from scipy.integrate import quad

from refundout.mixed import LaplaceLogistic, finite_hessian


def test_near_zero_variance_reduces_to_ordinary_logistic_likelihood():
    y = np.array([0, 1, 0, 1, 1, 0])
    x = np.c_[np.ones(6), [0, 0, 0, 1, 1, 1]]
    model = LaplaceLogistic(y, x, [["a", "a", "b", "b", "c", "c"]])
    theta = np.array([-0.7, 1.2, -14.0])
    expected = np.sum(np.logaddexp(0, x @ theta[:2]) - y * (x @ theta[:2]))
    assert abs(model.objective(theta) - expected) < 1e-8


def test_laplace_agrees_with_quadrature_for_well_informed_intercept():
    y = np.r_[np.zeros(40), np.ones(60)]
    x = np.ones((100, 1))
    model = LaplaceLogistic(y, x, [["a"] * 100])
    theta = np.array([0.1, np.log(0.5)])

    def density(u):
        eta = 0.1 + 0.5 * u
        return np.exp(np.sum(y * eta - np.logaddexp(0, eta)) - 0.5 * u * u) / np.sqrt(
            2 * np.pi
        )

    integral = quad(density, -10, 10, epsabs=1e-40)[0]
    assert abs(model.objective(theta) + np.log(integral)) < 0.01


def test_information_hessian():
    a = np.array([[3.0, 1.0], [1.0, 4.0]])
    got = finite_hessian(lambda x: 0.5 * x @ a @ x, np.array([0.4, -0.5]), [0, 1])
    assert np.allclose(got, a, atol=1e-7)
