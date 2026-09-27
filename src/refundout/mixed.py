"""Frequentist random-intercept logistic GLMM by Laplace maximum likelihood.

Standard-normal latent intercepts avoid cancellation near zero variance. The exact integrand is
Bernoulli likelihood × independent standard-normal densities; Newton solves its conditional mode.
Reference convention: lme4 glmer nAGQ=1 (https://lme4.github.io/lme4/reference/glmer.html).
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.sparse.linalg import splu
from scipy.special import expit
from scipy.stats import norm


class LaplaceLogistic:
    def __init__(self, y, x, groups):
        self.y = np.asarray(y, float)
        self.x = np.asarray(x, float)
        self.p = self.x.shape[1]
        blocks = []
        self.sizes = []
        for group in groups:
            _, indices = np.unique(np.asarray(group), return_inverse=True)
            n = int(indices.max()) + 1
            blocks.append(
                sparse.csc_matrix(
                    (np.ones(len(y)), (np.arange(len(y)), indices)), shape=(len(y), n)
                )
            )
            self.sizes.append(n)
        self.z = sparse.hstack(blocks, format="csc")
        self.q = self.z.shape[1]

    def objective(self, theta):
        beta = theta[: self.p]
        scales = np.repeat(np.exp(theta[self.p :]), self.sizes)
        z = self.z.multiply(scales).tocsc()
        offset = self.x @ beta
        u = np.zeros(self.q)

        def joint(v):
            eta = offset + z @ v
            return np.sum(np.logaddexp(0, eta) - self.y * eta) + 0.5 * (v @ v)

        value = joint(u)
        for iteration in range(80):
            eta = offset + z @ u
            mu = expit(eta)
            w = np.maximum(mu * (1 - mu), 1e-12)
            h = (
                z.T @ z.multiply(w[:, None]) + sparse.eye(self.q, format="csc")
            ).tocsc()
            grad = np.asarray(z.T @ (mu - self.y)).ravel() + u
            step = splu(h).solve(grad)
            if np.max(np.abs(grad)) < 1e-7:
                break
            alpha = 1.0
            while alpha > 1e-8:
                candidate = u - alpha * step
                new = joint(candidate)
                if new <= value + 1e-10:
                    break
                alpha *= 0.5
            u = candidate
            value = new
        else:
            raise RuntimeError("Conditional mode did not converge")
        eta = offset + z @ u
        mu = expit(eta)
        w = np.maximum(mu * (1 - mu), 1e-12)
        h = (z.T @ z.multiply(w[:, None]) + sparse.eye(self.q, format="csc")).tocsc()
        logdet = np.log(np.abs(splu(h).U.diagonal())).sum()
        return float(joint(u) + 0.5 * logdet)

    def fit(self):
        starts = [
            np.r_[np.zeros(self.p), np.full(len(self.sizes), v)] for v in [-1.0, 0.5]
        ]
        fits = [
            minimize(
                self.objective,
                start,
                method="L-BFGS-B",
                bounds=[(-25, 25)] * self.p + [(-7, 4)] * len(self.sizes),
                options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-5, "maxls": 40},
            )
            for start in starts
        ]
        best = min(fits, key=lambda r: r.fun)
        # Recheck the best basin from perturbations; variance boundaries can trap other starts.
        for delta in [-0.3, 0.3]:
            start = best.x.copy()
            start[self.p :] = np.clip(start[self.p :] + delta, -7, 4)
            fits.append(
                minimize(
                    self.objective,
                    start,
                    method="L-BFGS-B",
                    bounds=[(-25, 25)] * self.p + [(-7, 4)] * len(self.sizes),
                    options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-5, "maxls": 40},
                )
            )
        best = min(fits, key=lambda r: r.fun)
        theta = best.x
        # Boundary variances are held fixed when estimating curvature of the free parameters.
        free = [i for i, v in enumerate(theta) if i < self.p or -6.95 < v < 3.95]
        hessian = finite_hessian(self.objective, theta, free)
        eig = np.linalg.eigvalsh(hessian)
        cov = np.linalg.inv(hessian) if eig.min() > 0 else np.full_like(hessian, np.nan)
        se = np.sqrt(np.diag(cov)[: self.p])
        beta = theta[: self.p]
        close = sum(r.success and abs(r.fun - best.fun) < 0.01 for r in fits) >= 2
        usable = bool(
            best.success
            and close
            and np.all(np.isfinite(se))
            and not any(abs(v) > 24.9 for v in beta)
        )
        return {
            "method": "Laplace maximum likelihood; approximate Wald CI",
            "beta": beta.tolist(),
            "se": se.tolist(),
            "odds_ratio": float(np.exp(beta[1])),
            "ci95": np.exp(beta[1] + np.array([-1, 1]) * 1.96 * se[1]).tolist(),
            "p_value": float(2 * norm.sf(abs(beta[1] / se[1]))),
            "random_sd": dict(
                zip(["base", "paraphrase", "task"], np.exp(theta[self.p :]).tolist())
            ),
            "boundary_components": [
                i for i, v in enumerate(theta[self.p :]) if v <= -6.95 or v >= 3.95
            ],
            "usable": usable,
            "min_information_eigenvalue": float(eig.min()),
            "free_information_indices": free,
            "fits": [
                {
                    "success": bool(r.success),
                    "message": str(r.message),
                    "nll": float(r.fun),
                    "theta": r.x.tolist(),
                }
                for r in fits
            ],
        }


def finite_hessian(fun, point, indices, step=0.002):
    n = len(indices)
    out = np.zeros((n, n))
    f = fun(point)
    for a, i in enumerate(indices):
        ei = np.zeros(len(point))
        ei[i] = step
        out[a, a] = (fun(point + ei) - 2 * f + fun(point - ei)) / step**2
        for b, j in enumerate(indices[:a]):
            ej = np.zeros(len(point))
            ej[j] = step
            out[a, b] = out[b, a] = (
                fun(point + ei + ej)
                - fun(point + ei - ej)
                - fun(point - ei + ej)
                + fun(point - ei - ej)
            ) / (4 * step**2)
    return out
