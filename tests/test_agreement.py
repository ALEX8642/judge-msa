import numpy as np
import pandas as pd
import pytest

from judge_msa.agreement import between_judges, cohen_kappa, vs_reference, within_judge
from judge_msa.simulate import JudgeSpec, simulate
from judge_msa.table import NotEstimable, validate


def test_cohen_kappa_textbook():
    # 2x2 table [[20, 5], [10, 15]] -> kappa 0.40
    a = ["y"] * 25 + ["n"] * 25
    b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    assert cohen_kappa(pd.Series(a), pd.Series(b)) == pytest.approx(0.40, abs=1e-9)


def test_perfect_agreement():
    df = simulate(200, {"A": 0.5}, {"j": JudgeSpec(), "k": JudgeSpec()}, 3, seed=0)
    w = within_judge(df).set_index("judge")
    assert w.loc["j", "pct_all_agree"] == 1.0
    assert w.loc["j", "flip_rate"] == 0.0
    assert w.loc["j", "fleiss_kappa"] == pytest.approx(1.0)
    b = between_judges(df)
    assert b["pct_all_agree"] == 1.0
    assert b["fleiss_kappa"] == pytest.approx(1.0)
    assert b["pairwise"]["cohen_kappa"].iloc[0] == pytest.approx(1.0)


def test_flip_rate_recovered():
    df = simulate(5000, {"A": 0.6}, {"j": JudgeSpec(flip=0.1)}, 5, seed=1)
    w = within_judge(df).iloc[0]
    assert w["flip_rate"] == pytest.approx(2 * 0.1 * 0.9, abs=0.01)
    assert w["n_trials"] == 5
    assert w["n_parts"] == 5000
    assert 0 < w["fleiss_kappa"] < 1


def test_miss_and_false_alarm_recovered():
    spec = JudgeSpec(miss=0.3, false_alarm=0.1)
    df = simulate(6000, {"A": 0.6}, {"j": spec}, 2, seed=2)
    r = vs_reference(df, "pass").iloc[0]
    assert r["miss_rate"] == pytest.approx(0.3, abs=0.02)
    assert r["false_alarm_rate"] == pytest.approx(0.1, abs=0.02)
    assert 0 < r["cohen_kappa"] < 1
    assert r["n_parts"] == 6000


def test_vs_reference_by_group():
    spec = JudgeSpec(miss={"A": 0.4, "B": 0.0})
    df = simulate(4000, {"A": 0.5, "B": 0.5}, {"j": spec}, 1, seed=3)
    r = vs_reference(df, "pass", by="system").set_index("system")
    assert r.loc["A", "miss_rate"] == pytest.approx(0.4, abs=0.03)
    assert r.loc["B", "miss_rate"] == pytest.approx(0.0, abs=0.001)


def test_one_trial_not_estimable():
    df = simulate(50, {"A": 0.5}, {"j": JudgeSpec(flip=0.1)}, 1, seed=4)
    w = within_judge(df).iloc[0]
    for col in ("pct_all_agree", "flip_rate", "fleiss_kappa"):
        assert isinstance(w[col], NotEstimable)


def test_no_variation_kappa_not_estimable():
    df = validate(
        pd.DataFrame(
            {
                "item": [f"q{i}" for i in range(5)] * 4,
                "judge": ["j"] * 10 + ["k"] * 10,
                "trial": ([0] * 5 + [1] * 5) * 2,
                "verdict": "pass",
            }
        )
    )
    w = within_judge(df).iloc[0]
    assert isinstance(w["fleiss_kappa"], NotEstimable)
    assert "no variation" in w["fleiss_kappa"].reason
    assert w["pct_all_agree"] == 1.0
    b = between_judges(df)
    assert isinstance(b["fleiss_kappa"], NotEstimable)
    assert b["pct_all_agree"] == 1.0


def test_one_judge_between_not_estimable():
    df = simulate(20, {"A": 0.5}, {"j": JudgeSpec()}, 2, seed=5)
    assert isinstance(between_judges(df), NotEstimable)


def test_no_reference_not_estimable():
    df = simulate(20, {"A": 0.5}, {"j": JudgeSpec()}, 2, ref_fraction=0.0, seed=5)
    assert isinstance(vs_reference(df, "pass"), NotEstimable)


def test_unequal_trials_do_not_raise():
    df = simulate(300, {"A": 0.5}, {"j": JudgeSpec(flip=0.2), "k": JudgeSpec(flip=0.2)}, 4, seed=6)
    rng = np.random.default_rng(0)
    df = validate(df[rng.random(len(df)) > 0.2])
    w = within_judge(df)
    assert (w["n_parts"] > 0).all()
    assert all(0 < v < 1 for v in w["flip_rate"])
    assert all(isinstance(v, float) for v in w["fleiss_kappa"])
    assert isinstance(between_judges(df)["fleiss_kappa"], float)


def test_three_categories_supported():
    rng = np.random.default_rng(1)
    n = 300
    base = rng.choice(["correct", "wrong", "declined"], n)
    rows = []
    for j in ("j", "k"):
        for t in range(2):
            noisy = np.where(
                rng.random(n) < 0.1, rng.choice(["correct", "wrong", "declined"], n), base
            )
            rows.append(
                pd.DataFrame(
                    {"item": np.arange(n).astype(str), "judge": j, "trial": t, "verdict": noisy}
                )
            )
    df = validate(pd.concat(rows))
    assert 0.5 < within_judge(df)["fleiss_kappa"].iloc[0] < 1
    assert 0.5 < between_judges(df)["fleiss_kappa"] < 1


def test_fleiss_matches_statsmodels_for_equal_raters():
    from statsmodels.stats.inter_rater import fleiss_kappa as sm_fleiss

    from judge_msa.agreement import fleiss_kappa

    rng = np.random.default_rng(7)
    counts = rng.multinomial(6, [0.5, 0.3, 0.2], size=80)
    assert fleiss_kappa(counts) == pytest.approx(sm_fleiss(counts), abs=1e-12)


def test_vs_reference_uses_weights():
    df = pd.DataFrame(
        {
            "item": ["a", "b", "c", "d"],
            "judge": "j",
            "trial": 0,
            "verdict": ["pass", "fail", "pass", "fail"],
            "reference": ["pass", "pass", "fail", "fail"],
            "weight": [1.0, 3.0, 1.0, 1.0],
        }
    )
    r = vs_reference(validate(df), "pass").iloc[0]
    assert r["false_alarm_rate"] == pytest.approx(3 / 4)
    assert r["miss_rate"] == pytest.approx(1 / 2)
    assert r["agreement"] == pytest.approx(2 / 6)
