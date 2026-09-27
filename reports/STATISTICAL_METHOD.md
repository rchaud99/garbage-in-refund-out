# Statistical implementation

The primary model is a custom sparse Laplace maximum-likelihood logistic mixed model in
`src/refundout/mixed.py`, with standard-normal latent effects rescaled by three estimated standard deviations.
It follows the nAGQ=1 integration convention documented for [lme4 glmer](https://lme4.github.io/lme4/reference/glmer.html).
It was not fitted with lme4. R is unavailable on this Mac; `scripts/verify_glmm.R` is an optional independent check that has not been run.

The objective minimizes the conditional Bernoulli negative log likelihood plus half the squared latent
effects and half the log determinant of the conditional information matrix. Newton iteration solves
the conditional mode; bounded numerical optimization estimates the fixed coefficients and log standard
deviations. Multiple starts and perturbations check the best basin. The fixed-effect covariance comes
from a numerical Hessian of the marginal objective, omitting nuisance variance parameters on the imposed
near-zero boundary. These are approximate Wald confidence intervals, with weak support for estimating
three task and six paraphrase effects; they are not exact small-sample intervals.

Tests compare the near-zero-variance likelihood with ordinary logistic likelihood and a one-group case
with numerical quadrature. A deterministic simulation with true OR 4.48 produced an estimate of 3.61
and a 95% interval [2.81, 4.64]. This is a numerical sanity check, not a coverage study. Diagnostics and
all optimizer starts are saved in power-results.json.

Descriptive intervals use 10,000 percentile bootstrap resamples of independent bases/orders, preserving
all repeats and wording results on a base. A zero-event sample necessarily yields a degenerate bootstrap
interval; no equivalence or zero-risk claim is made.
