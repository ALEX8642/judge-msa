import pytest

from judge_msa.components import components, repeatability_var
from judge_msa.simulate import JudgeSpec, simulate
from judge_msa.table import NotEstimable


def test_repeatability_variance_recovered():
    df = simulate(5000, {"A": 0.6}, {"j": JudgeSpec(flip=0.1)}, 5, seed=0)
    r = repeatability_var(df, "pass").iloc[0]
    assert r["v"] == pytest.approx(0.09, abs=0.005)
    assert r["n_parts_used"] == 5000


def test_zero_flip_no_repeatability_share():
    df = simulate(500, {"A": 0.6}, {"j": JudgeSpec(), "k": JudgeSpec()}, 3, seed=1)
    c = components(df, "pass").set_index("component")
    assert c.loc["repeatability", "variance"] == 0.0
    assert c.loc["judge_x_part", "variance"] == 0.0
    assert c.loc["part", "share"] == pytest.approx(1.0)
    assert c.attrs["grr_share"] == pytest.approx(0.0)


def test_independent_judge_errors_show_as_judge_x_part():
    spec = JudgeSpec(miss=0.3, false_alarm=0.3)
    df = simulate(3000, {"A": 0.5}, {"j": spec, "k": spec}, 2, seed=2)
    c = components(df, "pass").set_index("component")
    # a judge's latent verdict given the truth is Bernoulli(0.7 or 0.3): variance 0.21
    assert c.loc["judge_x_part", "variance"] == pytest.approx(0.21, abs=0.02)
    assert c.loc["repeatability", "variance"] == 0.0
    assert 0 < c.attrs["grr_share"] < 1


def test_lenient_judge_shows_as_judge_main_effect():
    df = simulate(
        4000, {"A": 0.5}, {"strict": JudgeSpec(false_alarm=0.4), "fair": JudgeSpec()}, 1, seed=3
    )
    c = components(df, "pass").set_index("component")
    # judge means 0.3 and 0.5 -> variance of two means = 0.02
    assert c.loc["judge", "variance"] == pytest.approx(0.02, abs=0.006)


def test_shares_sum_to_one():
    spec = JudgeSpec(flip=0.1, miss=0.2)
    df = simulate(800, {"A": 0.6, "B": 0.4}, {"j": spec, "k": spec, "l": spec}, 3, seed=4)
    c = components(df, "pass")
    assert sum(c["share"]) == pytest.approx(1.0)


def test_one_trial_and_one_judge_not_estimable():
    df = simulate(100, {"A": 0.6}, {"j": JudgeSpec(flip=0.1)}, 1, seed=5)
    assert isinstance(repeatability_var(df, "pass").iloc[0]["v"], NotEstimable)
    c = components(df, "pass").set_index("component")
    assert isinstance(c.loc["repeatability", "variance"], NotEstimable)
    assert isinstance(c.loc["judge", "variance"], NotEstimable)
    assert isinstance(c.loc["part", "variance"], float)
