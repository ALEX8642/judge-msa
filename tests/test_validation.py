"""Statistical validation by simulation: do the estimators recover planted truth?

Slow. Run with ``pytest -m slow``. Results are summarised in docs/validation.md.
"""

import numpy as np
import pytest

from judge_msa.bias import differential_bias
from judge_msa.mrd import mrd
from judge_msa.simulate import JudgeSpec, expected, simulate
from judge_msa.table import validate

pytestmark = pytest.mark.slow

BIASED = JudgeSpec(flip=0.05, miss={"A": 0.25, "B": 0.05})
SYSTEMS = {"A": 0.7, "B": 0.7}


def planted_diff_bias(spec=BIASED, systems=SYSTEMS):
    return expected(spec, "A", systems["A"])["bias"] - expected(spec, "B", systems["B"])["bias"]


def coverage(n_sims=200, n_items=300, n_boot=400):
    target = planted_diff_bias()
    hits = 0
    for s in range(n_sims):
        df = simulate(n_items, SYSTEMS, {"j": BIASED}, 3, seed=1000 + s)
        d = differential_bias(df, "pass", "A", "B", n_boot=n_boot, seed=s).iloc[0]
        hits += d["ci_lo"] <= target <= d["ci_hi"]
    return hits / n_sims


def exceedance(n_sims=300, n_items=170, ref_items=50, n_boot=400, spec=BIASED):
    """How often the judged difference misses the true difference by more than the MRD."""
    over = 0
    for s in range(n_sims):
        full = simulate(n_items, SYSTEMS, {"j": spec}, 3, seed=5000 + s)
        truth = full.drop_duplicates(["item", "system"]).assign(
            t=lambda d: d["reference"] == "pass"
        )
        true_diff = truth.groupby("system")["t"].mean()
        true_diff = true_diff["A"] - true_diff["B"]
        keep = set(np.random.default_rng(s).permutation(full["item"].unique())[:ref_items])
        df = full.copy()
        df.loc[~df["item"].isin(keep), "reference"] = None
        r = mrd(validate(df), "pass", "j", "A", "B", n_boot=n_boot, seed=s)
        over += abs(r.diff_observed - true_diff) > r.mrd
    return over / n_sims


def bias_bound_median(n_items, n_sims=40):
    spec = JudgeSpec(flip=0.05)
    out = []
    for s in range(n_sims):
        df = simulate(n_items, SYSTEMS, {"j": spec}, 3, seed=9000 + s)
        out.append(mrd(df, "pass", "j", "A", "B", n_boot=300, seed=s).bias_bound)
    return float(np.median(out))


def test_differential_bias_interval_coverage():
    assert coverage() >= 0.90


def test_mrd_is_conservative_under_planted_bias():
    assert exceedance() <= 0.05


def test_mrd_is_conservative_without_bias():
    assert exceedance(spec=JudgeSpec(flip=0.05)) <= 0.05


def test_bias_bound_shrinks_with_more_reference_items():
    assert bias_bound_median(2000) < 0.5 * bias_bound_median(200)
