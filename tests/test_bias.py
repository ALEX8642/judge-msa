import time

import pytest

from judge_msa.bias import bias_table, difference_by_judge, differential_bias
from judge_msa.simulate import JudgeSpec, expected, simulate
from judge_msa.table import NotEstimable

SPEC = JudgeSpec(flip=0.05, miss={"A": 0.3, "B": 0.05})
SYSTEMS = {"A": 0.6, "B": 0.6}
PLANTED = expected(SPEC, "A", 0.6)["bias"] - expected(SPEC, "B", 0.6)["bias"]


def test_bias_table_recovers_planted_bias():
    df = simulate(4000, SYSTEMS, {"j": SPEC}, 2, seed=0)
    t = bias_table(df, "pass", n_boot=300).set_index("system")
    for s in ("A", "B"):
        exp = expected(SPEC, s, 0.6)["bias"]
        assert t.loc[s, "bias"] == pytest.approx(exp, abs=0.02)
        assert t.loc[s, "ci_lo"] <= exp <= t.loc[s, "ci_hi"]
        assert t.loc[s, "n_parts"] == 4000
        assert t.loc[s, "bias"] == pytest.approx(t.loc[s, "judge_score"] - t.loc[s, "ref_score"])


def test_differential_bias_recovered_and_covered():
    df = simulate(4000, SYSTEMS, {"j": SPEC}, 2, seed=1)
    d = differential_bias(df, "pass", "A", "B", n_boot=300).iloc[0]
    assert d["diff_bias"] == pytest.approx(PLANTED, abs=0.02)
    assert d["ci_lo"] <= PLANTED <= d["ci_hi"]


def test_only_reference_parts_are_used():
    df = simulate(2000, SYSTEMS, {"j": SPEC}, 1, ref_fraction=0.25, seed=2)
    t = bias_table(df, "pass", n_boot=100)
    assert (t["n_parts"] == 500).all()


def test_no_reference():
    df = simulate(100, SYSTEMS, {"j": SPEC}, 1, ref_fraction=0.0, seed=3)
    assert isinstance(bias_table(df, "pass"), NotEstimable)
    assert isinstance(differential_bias(df, "pass", "A", "B"), NotEstimable)


def test_bootstrap_deterministic_for_seed():
    df = simulate(300, SYSTEMS, {"j": SPEC}, 2, seed=4)
    a = differential_bias(df, "pass", "A", "B", n_boot=200, seed=9)
    b = differential_bias(df, "pass", "A", "B", n_boot=200, seed=9)
    assert a.equals(b)


def test_interval_narrows_with_more_items():
    def width(n):
        d = differential_bias(
            simulate(n, SYSTEMS, {"j": SPEC}, 2, seed=5), "pass", "A", "B", n_boot=300
        ).iloc[0]
        return d["ci_hi"] - d["ci_lo"]

    assert width(4000) < width(500)


def test_difference_by_judge_and_spread():
    judges = {"strict": JudgeSpec(false_alarm={"A": 0.3, "B": 0.0}), "fair": JudgeSpec()}
    df = simulate(3000, SYSTEMS, judges, 1, ref_fraction=0.0, seed=6)
    t = difference_by_judge(df, "pass", "A", "B", n_boot=100).set_index("judge")
    assert t.loc["fair", "diff"] == pytest.approx(0.0, abs=0.04)
    assert t.loc["strict", "diff"] == pytest.approx(-0.18, abs=0.04)
    assert t.attrs["spread"] == pytest.approx(0.18, abs=0.05)


def test_by_extra_column():
    df = simulate(1000, {"A": 0.6}, {"j": JudgeSpec(miss=0.2)}, 1, seed=7)
    df["category"] = ["table" if int(i[1:]) % 2 else "text" for i in df["item"]]
    t = bias_table(df, "pass", by="category", n_boot=100)
    assert set(t["category"]) == {"table", "text"}


def test_bootstrap_is_fast_enough():
    df = simulate(338, SYSTEMS, {"a": SPEC, "b": SPEC, "c": SPEC}, 5, seed=8)
    t0 = time.perf_counter()
    differential_bias(df, "pass", "A", "B")
    assert time.perf_counter() - t0 < 10
