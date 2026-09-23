"""Deterministic S1 generators: stdlib GP-EI and (1+1) reimplementations."""
from bisect import bisect_right
from functools import lru_cache
import hashlib
from itertools import accumulate
import math

from . import b5_generator_contrast as B

NAMESPACE = "t2849-harness-v1"
LENGTH_SCALES = (0.25, 0.5, 1., 2.)
SIGNAL_VARIANCES = (0.25, 1., 4.)
NOISE = math.log(1.03) ** 2
JITTER = 1e-10
NUMERICS = {"x": "ln(v)", "y": "ln(tps), centered on training mean",
            "kernel": "Matern-5/2", "length_scales": LENGTH_SCALES,
            "signal_variances": SIGNAL_VARIANCES, "noise": NOISE, "jitter": JITTER,
            "evolution_lambda": math.log(4), "rounding": "floor(exp(x)+0.5)",
            "calibrated": False}


def coordinates(workload, series, a=1):
    if (workload not in B.WORKLOADS or type(series) is not int or series < 1
            or type(a) is not int or a < 1):
        raise ValueError("invalid generator coordinates")


@lru_cache(maxsize=1)
def _weights():
    return B.weights_table()


def random_value(workload, series, a, *, namespace=NAMESPACE, arm="random",
                 excluded=(), weights=None):
    coordinates(workload, series, a)
    weights = _weights() if weights is None else weights
    pairs = [(v, w) for v, w in enumerate(weights, 1) if v not in excluded]
    if not pairs or any(type(w) is not int or w <= 0 for _, w in pairs):
        raise ValueError("empty support or invalid weights")
    cumulative = tuple(accumulate(w for _, w in pairs))
    total = cumulative[-1]
    if total > 2**256:
        raise ValueError("weight total exceeds hash space")
    limit = (2**256 // total) * total
    counter = 0
    while True:
        preimage = f"{namespace}|{arm}|{workload}|{series}|{a}|{counter}"
        uniform = int.from_bytes(hashlib.sha256(preimage.encode("ascii")).digest(), "big")
        if uniform < limit:
            return pairs[bisect_right(cumulative, uniform % total)][0], counter
        counter += 1


def sweep_order(workload, series, initial_values=(5, 10)):
    coordinates(workload, series)
    grid = [v for v in B.EXTENDED_SWEEP_US if 1 <= v <= 1000]
    if len(grid) != 28 or len(set(grid)) != 28:
        raise ValueError("sweep grid changed")
    return tuple(sorted((v for v in grid if v not in initial_values), key=lambda v: (
        hashlib.sha256(f"{NAMESPACE}|sweep|{workload}|{series}|{v}".encode()).digest(), v)))


def matern52(x, z, length_scale, signal_variance):
    """Kernel on log coordinates (the caller converts v to ln(v))."""
    d = math.sqrt(5) * abs(x - z) / length_scale
    return signal_variance * (1 + d + d*d/3) * math.exp(-d)


def _forward(lower, rhs):
    result = []
    for i, row in enumerate(lower):
        result.append((rhs[i] - sum(row[j]*result[j] for j in range(i))) / row[i])
    return result


def _fit(observations, length_scale, signal_variance, noise, jitter):
    xs = [math.log(v) for v, _ in observations]
    ys = [math.log(t) for _, t in observations]
    center = sum(ys)/len(ys)
    residual = [y-center for y in ys]
    lower = [[0.] * len(xs) for _ in xs]
    for i, x in enumerate(xs):
        for j in range(i+1):
            value = matern52(x, xs[j], length_scale, signal_variance)
            value += noise+jitter if i == j else 0
            value -= sum(lower[i][k]*lower[j][k] for k in range(j))
            lower[i][j] = math.sqrt(value) if i == j else value/lower[j][j]
    solved = _forward(lower, residual)
    alpha = [0.] * len(xs)
    for i in reversed(range(len(xs))):
        alpha[i] = (solved[i] - sum(lower[j][i]*alpha[j] for j in range(i+1, len(xs))))/lower[i][i]
    likelihood = (-sum(v*v for v in solved)/2 - sum(math.log(lower[i][i]) for i in range(len(xs)))
                  - len(xs)*math.log(2*math.pi)/2)
    return xs, center, lower, alpha, likelihood


def gp_posterior(observations, candidates, *, length_scale=None, signal_variance=None,
                 noise=NOISE, jitter=JITTER):
    if not observations or any(not B.validate_backoff_value(v).accepted or not B._positive(t)
                               for v, t in observations):
        raise ValueError("positive observations required")
    lengths = LENGTH_SCALES if length_scale is None else (length_scale,)
    signals = SIGNAL_VARIANCES if signal_variance is None else (signal_variance,)
    fits = [(l, s, _fit(observations, l, s, noise, jitter)) for l in lengths for s in signals]
    length, signal, fit = min(fits, key=lambda item: (-item[2][-1], item[0], item[1]))
    xs, center, lower, alpha, likelihood = fit
    means, variances = [], []
    for value in candidates:
        k = [matern52(math.log(value), x, length, signal) for x in xs]
        solved = _forward(lower, k)
        means.append(center + sum(a*b for a, b in zip(k, alpha)))
        variances.append(max(0., signal - sum(v*v for v in solved)))
    return {"means": means, "variances": variances, "log_likelihood": likelihood,
            "length_scale": length, "signal_variance": signal}


def expected_improvement(mean, variance, incumbent):
    if variance <= 0:
        return max(0., mean-incumbent)
    sigma = math.sqrt(variance)
    z = (mean-incumbent)/sigma
    return (mean-incumbent)*(1+math.erf(z/math.sqrt(2)))/2 + sigma*math.exp(-z*z/2)/math.sqrt(2*math.pi)


def normal(event):
    return (event.get("outcome") == "certified" and event.get("quality") == "normal"
            and not event.get("anomalies") and B._positive(event.get("fitness_tps")))


class BOGenerator:
    def __init__(self, workload, series):
        coordinates(workload, series)
        self.workload, self.series = workload, series
        self.observations, self.failed = [], set()

    def tell(self, event):
        value = event["value"]
        if normal(event):
            self.observations.append((value, event["fitness_tps"]))
        elif event.get("outcome") in {"rejected-tier0", "build-failed", "anomaly"} or event.get("anomalies"):
            self.failed.add(value)

    def ask(self, a):
        coordinates(self.workload, self.series, a)
        if not self.observations:
            return random_value(self.workload, self.series, a, arm="bo-fallback", excluded=self.failed)[0]
        candidates = [v for v in range(1, 1001) if v not in self.failed]
        if not candidates:
            raise ValueError("empty BO support")
        posterior = gp_posterior(self.observations, candidates)
        incumbent = max(math.log(t) for _, t in self.observations)
        ei = [expected_improvement(m, v, incumbent)
              for m, v in zip(posterior["means"], posterior["variances"])]
        return candidates[max(range(len(candidates)), key=lambda i: (ei[i], -candidates[i]))]


def mutate(parent, delta):
    child = min(1000, max(1, math.floor(math.exp(math.log(parent)+delta)+0.5)))
    if child == parent:
        child += 1 if delta >= 0 else -1
        if child < 1 or child > 1000:
            child = 2 if parent == 1 else 999
    return child


class EvolutionGenerator:
    def __init__(self, workload, series):
        coordinates(workload, series)
        self.workload, self.series, self.parent = workload, series, None

    def tell(self, event):
        if normal(event) and (self.parent is None or event["fitness_tps"] > self.parent[1]):
            self.parent = event["value"], event["fitness_tps"]

    def ask(self, a):
        coordinates(self.workload, self.series, a)
        if self.parent is None:
            return random_value(self.workload, self.series, a, arm="evolution-fallback")[0]
        preimage = f"{NAMESPACE}|evolution|{self.workload}|{self.series}|{a}|0"
        u = int.from_bytes(hashlib.sha256(preimage.encode()).digest(), "big") / (2**256-1)
        return mutate(self.parent[0], (2*u-1)*math.log(4))
