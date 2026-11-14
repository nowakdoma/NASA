import numpy as np

from engine.mcda import normalise_metrics, p_best, rank_strategies, sample_dirichlet_weights


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


def test_rank_strategies_parity():
    strategies = [
        {
            "id": "strat_poor",
            "name": "High Water Low Margin",
            "rotation": ["corn", "corn"],
            "metrics": {
                "water_use_mm": {"p10": 600, "p50": 650, "p90": 700},
                "income_usd_ha": {"p10": 50, "p50": 100, "p90": 150},
                "soil_index": {"p10": 0.2, "p50": 0.3, "p90": 0.4},
                "erosion_t_ha": {"p10": 5.0, "p50": 6.0, "p90": 7.0},
                "labour_index": {"p10": 0.7, "p50": 0.8, "p90": 0.9},
            },
        },
        {
            "id": "strat_ideal",
            "name": "Water Conserving High Soil",
            "rotation": ["sorghum", "wheat"],
            "metrics": {
                "water_use_mm": {"p10": 200, "p50": 250, "p90": 300},
                "income_usd_ha": {"p10": 250, "p50": 300, "p90": 350},
                "soil_index": {"p10": 0.7, "p50": 0.8, "p90": 0.9},
                "erosion_t_ha": {"p10": 1.0, "p50": 1.5, "p90": 2.0},
                "labour_index": {"p10": 0.2, "p50": 0.3, "p90": 0.4},
            },
        },
    ]

    priorities = {"water": 5, "income": 4, "soil": 5, "erosion": 4, "labour": 3}
    ranked = rank_strategies(strategies, priorities, n=1000, seed=42)

    assert len(ranked) == 2
    assert ranked[0]["strategy"]["id"] == "strat_ideal"
    assert ranked[0]["pBest"] > 0.95
    assert ranked[0]["medianScore"] > ranked[1]["medianScore"]
    assert np.isclose(ranked[0]["pBest"] + ranked[1]["pBest"], 1.0)


def test_rank_strategies_empty():
    assert rank_strategies([]) == []
