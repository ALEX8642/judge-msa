import math

import pandas as pd
import pytest

from judge_msa.mrd import mrd
from judge_msa.simulate import JudgeSpec, simulate
from judge_msa.table import NotEstimable, validate


def _hand_table():
    # 4 items x systems A, B; judge j; 2 trials. y per part (trial0, trial1):
    # A: (1,1) (1,0) (0,0) (1,0)  -> part variances 0, .5, 0, .5 -> v_A = 0.25
    # B: (1,1) (1,1) (0,0) (0,1)  -> part variances 0, 0, 0, .5  -> v_B = 0.125
    ya = [(1, 1), (1, 0), (0, 0), (1, 0)]
    yb = [(1, 1), (1, 1), (0, 0), (0, 1)]
    rows = []
    for s, ys in (("A", ya), ("B", yb)):
        for i, pair in enumerate(ys):
            for t, y in enumerate(pair):
                rows.append(
                    {
                        "item": f"q{i}",
                        "system": s,
                        "judge": "j",
                        "trial": t,
                        "verdict": "pass" if y else "fail",
                        "reference": "pass",
                    }
                )
    return validate(pd.DataFrame(rows))


def test_noise_matches_formula_by_hand():
    r = mrd(_hand_table(), "pass", "j", "A", "B", n_boot=50)
    assert r.n_items == 4 and r.n_trials == 2
    assert r.noise == pytest.approx(1.959963984540054 * math.sqrt((0.25 + 0.125) / (4 * 2)))
    # scores: A = (1 + .5 + 0 + .5)/4 = 0.5, B = (1 + 1 + 0 + .5)/4 = 0.625
    assert r.diff_observed == pytest.approx(-0.125)
    assert r.mrd == pytest.approx(r.noise + r.bias_bound)


def test_what_if_items_and_trials():
    t = _hand_table()
    base = mrd(t, "pass", "j", "A", "B", n_boot=50)
    more = mrd(t, "pass", "j", "A", "B", n_items=400, n_trials=2, n_boot=50)
    assert more.noise == pytest.approx(base.noise / 10)
    assert more.bias_bound == base.bias_bound


def test_zero_flip_zero_noise():
    df = simulate(300, {"A": 0.6, "B": 0.6}, {"j": JudgeSpec(miss=0.1)}, 3, seed=0)
    assert mrd(df, "pass", "j", "A", "B", n_boot=100).noise == 0.0


def test_bias_bound_reflects_planted_bias():
    spec = JudgeSpec(flip=0.05, miss={"A": 0.3, "B": 0.0})
    df = simulate(2000, {"A": 0.6, "B": 0.6}, {"j": spec}, 2, seed=1)
    r = mrd(df, "pass", "j", "A", "B", n_boot=300)
    assert r.bias_bound > 0.08
    assert r.diff_bias_ci[0] <= r.diff_bias <= r.diff_bias_ci[1]
    assert r.mrd > r.bias_bound


def test_no_reference():
    df = simulate(
        200, {"A": 0.6, "B": 0.6}, {"j": JudgeSpec(flip=0.1)}, 2, ref_fraction=0.0, seed=2
    )
    r = mrd(df, "pass", "j", "A", "B")
    assert isinstance(r.bias_bound, NotEstimable)
    assert isinstance(r.mrd, NotEstimable)
    assert isinstance(r.noise, float)
    assert any("bias unknown" in n for n in r.notes)


def test_one_trial():
    df = simulate(200, {"A": 0.6, "B": 0.6}, {"j": JudgeSpec(flip=0.1)}, 1, seed=3)
    r = mrd(df, "pass", "j", "A", "B", n_boot=50)
    assert isinstance(r.noise, NotEstimable)
    assert isinstance(r.mrd, NotEstimable)
    assert isinstance(r.bias_bound, float)


def test_unknown_judge_raises():
    with pytest.raises(ValueError, match="nobody"):
        mrd(_hand_table(), "pass", "nobody", "A", "B")
