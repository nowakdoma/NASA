import numpy as np

from engine.mcda import normalise_metrics, p_best, sample_dirichlet_weights


def test_normalise_direction():
    v = np.array([[1.0, 10.0], [3.0, 30.0]])
    out = normalise_metrics(v, np.array([True, False]))
    assert out.tolist() == [[1.0, 0.0], [0.0, 1.0]]


def test_dirichlet_rows_sum_to_one():
    w = sample_dirichlet_weights(np.array([1, 2, 0, 1, 1]), 20, 100, np.random.default_rng(0))
    assert w.shape == (100, 5)
    assert np.allclose(w.sum(axis=1), 1)


def test_p_best_dominant_strategy_wins():
    p50 = np.array([[10.0, 1.0], [5.0, 5.0]])  # metric0 lower-better, metric1 higher-better
    p10, p90 = p50 * 0.95, p50 * 1.05
    pb = p_best(p10, p50, p90, np.array([1.0, 1.0]), np.array([True, False]), n=500)
    assert np.isclose(pb.sum(), 1)
    assert pb[1] > 0.95
