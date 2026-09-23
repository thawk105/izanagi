"""Independent scalar/2x2 numerical oracles; no production Cholesky in expectations."""
import hashlib
import math
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import t2849_generators as G


def observation(value, fitness=100, **changes):
    return dict(value=value, fitness_tps=fitness, outcome="certified", quality="normal", **changes)


def kernel(v, w, length=1, signal=1):
    d = abs(math.log(v/w))/length
    return signal*(1+math.sqrt(5)*d+5*d*d/3)*math.exp(-math.sqrt(5)*d)


def test_gp_two_point_independent_values():
    observations = [(2, 100), (20, 400)]
    center = math.log(200)
    a = 1 + math.log(1.03)**2 + 1e-10
    b = kernel(2, 20)
    determinant = a*a-b*b
    y = [-math.log(2), math.log(2)]
    alpha = [(a*y[0]-b*y[1])/determinant, (a*y[1]-b*y[0])/determinant]
    posterior = G.gp_posterior(observations, [2, 5, 50], length_scale=1, signal_variance=1)
    for i, v in enumerate([2, 5, 50]):
        k, l = kernel(v, 2), kernel(v, 20)
        assert posterior["means"][i] == pytest.approx(center+k*alpha[0]+l*alpha[1])
        assert posterior["variances"][i] == pytest.approx(1-(a*k*k-2*b*k*l+a*l*l)/determinant)
    likelihood = -sum(x*z for x, z in zip(y, alpha))/2-math.log(determinant)/2-math.log(2*math.pi)
    assert posterior["log_likelihood"] == pytest.approx(likelihood)


def test_ei_latent_variance(monkeypatch):
    posterior = G.gp_posterior([(1, 100)], [1, 10], length_scale=1, signal_variance=1)
    for i, v in enumerate([1, 10]):
        variance = 1-kernel(v, 1)**2/(1+math.log(1.03)**2+1e-10)
        assert posterior["means"][i] == pytest.approx(math.log(100))
        assert posterior["variances"][i] == pytest.approx(variance)
        assert G.expected_improvement(posterior["means"][i], posterior["variances"][i], math.log(100)) == pytest.approx(math.sqrt(variance/(2*math.pi)))
    # One observation selects signal=.25 by likelihood and length=.25 by tie.
    # Observe the real ask -> posterior -> EI path without replacing its math.
    real_ei = G.expected_improvement
    scores = []
    def checked_ei(mean, variance, incumbent):
        value = len(scores) + 1
        expected_variance = .25-kernel(value, 1000, .25, .25)**2/(.25+math.log(1.03)**2+1e-10)
        expected = math.sqrt(expected_variance/(2*math.pi))
        assert mean == pytest.approx(math.log(100))
        assert incumbent == pytest.approx(math.log(100))
        assert variance == pytest.approx(expected_variance)
        actual = real_ei(mean, variance, incumbent)
        assert actual == pytest.approx(expected)
        scores.append(expected)
        return actual
    monkeypatch.setattr(G, "expected_improvement", checked_ei)
    bo = G.BOGenerator("balanced", 1)
    bo.tell(observation(1000))
    selected = bo.ask(1)
    assert len(scores) == 1000
    assert selected == max(range(1, 1001), key=lambda v: (scores[v-1], -v))


def test_bo_excludes_candidate_failures():
    bo = G.BOGenerator("balanced", 1)
    for v in range(1, 1000):
        bo.tell({"value": v, "outcome": "rejected-tier0"})
    assert bo.ask(1) == 1000
    bo.tell({"value": 1000, "outcome": "certified", "quality": "quality-missing"})
    assert bo.ask(2) == 1000
    bo.tell(observation(1000))
    assert bo.ask(3) == 1000
    bo.tell({"value": 1000, "outcome": "anomaly"})
    with pytest.raises(ValueError):
        bo.ask(4)


def test_bo_full_domain_and_hyperparameter_likelihood():
    obs = [(5, 200), (10, 100)]
    fits = [(G.gp_posterior(obs, [], length_scale=l, signal_variance=s)["log_likelihood"], l, s)
            for l in G.LENGTH_SCALES for s in G.SIGNAL_VARIANCES]
    best = min(fits, key=lambda x: (-x[0], x[1], x[2]))
    p = G.gp_posterior(obs, range(1, 1001))
    assert (p["length_scale"], p["signal_variance"]) == best[1:]
    bo = G.BOGenerator("balanced", 13)
    for v, f in obs:
        bo.tell(observation(v, f))
    eis = [G.expected_improvement(m, v, math.log(200)) for m, v in zip(p["means"], p["variances"])]
    assert bo.ask(31) == max(range(1, 1001), key=lambda v: (eis[v-1], -v))


def test_equal_fitness_keeps_parent():
    evo = G.EvolutionGenerator("balanced", 1)
    evo.tell(observation(10))
    evo.tell(observation(5))
    assert evo.parent == (10, 100)
    evo.tell({"value": 1, "outcome": "anomaly", "fitness_tps": 1000})
    assert evo.parent == (10, 100)
    evo.tell(observation(20, 101))
    assert evo.parent == (20, 101)


@pytest.mark.parametrize("parent,delta,expected", [(10, math.log(4), 40), (10, -math.log(4), 3),
    (10, 0, 11), (10, -1e-9, 9), (1, -1e-9, 2), (1000, 0, 999)])
def test_evolution_rounding(parent, delta, expected):
    assert G.mutate(parent, delta) == expected


def test_random_and_sweep_independent_preimages():
    weights = G.B.weights_table()
    for a in range(1, 8):
        u = int.from_bytes(hashlib.sha256(f"t2849-harness-v1|random|balanced|17|{a}|0".encode()).digest(), "big")
        residual = u % sum(weights)
        for v, w in enumerate(weights, 1):
            residual -= w
            if residual < 0:
                break
        assert G.random_value("balanced", 17, a) == (v, 0)
    grid = (1, 2, 3, 4, 6, 8, 12, 15, 20, 25, 35, 50, 75, 100, 150, 200,
            250, 300, 400, 500, 560, 600, 700, 800, 900, 1000)
    expected = tuple(sorted(grid, key=lambda v: hashlib.sha256(f"t2849-harness-v1|sweep|balanced|17|{v}".encode()).digest()))
    assert G.sweep_order("balanced", 17) == expected
    # Fixed vectors from independent Decimal-130 weights and SHA-256 preimages.
    assert [G.random_value("balanced", 17, a)[0] for a in range(1, 8)] == [2, 668, 15, 39, 6, 5, 95]
    assert expected == (600, 75, 800, 150, 1000, 1, 3, 560, 20, 250, 700, 15, 300,
                        6, 100, 2, 900, 12, 25, 8, 50, 35, 200, 400, 500, 4)


def test_rejection_sampling_exact_limit():
    # Find a real preimage with L=U0 and U1<L; no replacement hash function.
    def uniform(a, c):
        return int.from_bytes(hashlib.sha256(f"t2849-harness-v1|random|balanced|17|{a}|{c}".encode()).digest(), "big")
    a = next(a for a in range(1, 100) if uniform(a, 0) > 2**255 and uniform(a, 1) < uniform(a, 0))
    assert G.random_value("balanced", 17, a, weights=(uniform(a, 0),)) == (1, 1)


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
