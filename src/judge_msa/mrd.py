"""Minimum resolvable difference: the smallest gap between two systems a judge can be trusted on."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from judge_msa.bias import difference_by_judge, differential_bias
from judge_msa.bootstrap import DEFAULT_N_BOOT
from judge_msa.components import repeatability_var
from judge_msa.table import NotEstimable

Z95 = 1.959963984540054


@dataclass
class MRDResult:
    judge: str
    a: str
    b: str
    n_items: int
    n_trials: int
    diff_observed: float
    noise: float | NotEstimable
    bias_bound: float | NotEstimable
    mrd: float | NotEstimable
    diff_bias: float | NotEstimable
    diff_bias_ci: tuple[float, float] | NotEstimable
    notes: list[str] = field(default_factory=list)


def mrd(
    df: pd.DataFrame,
    positive: str,
    judge: str,
    a: str,
    b: str,
    *,
    n_items: int | None = None,
    n_trials: int | None = None,
    n_boot: int = DEFAULT_N_BOOT,
    seed: int = 0,
) -> MRDResult:
    """MRD = bias_bound + noise for comparing systems ``a`` and ``b`` with one judge.

    noise = 1.96 * sqrt((v_a + v_b) / (n_items * n_trials)): trial-to-trial variation of the judge,
    which more trials or items shrink. bias_bound = the larger absolute end of the 95% interval of
    the differential bias against the reference, which they do not.
    """
    d = df[(df["judge"] == judge) & df["system"].isin([a, b])]
    if d.empty:
        raise ValueError(f"no verdicts for judge {judge!r} on systems {a!r}, {b!r}")
    notes: list[str] = []
    per_item = d.groupby("item")["system"].nunique()
    n = n_items or int((per_item == 2).sum())
    k = n_trials or int(d.groupby(["item", "system"]).size().median())
    diff_observed = float(difference_by_judge(d, positive, a, b, n_boot=1).iloc[0]["diff"])

    rv = repeatability_var(d, positive).set_index("system")["v"]
    va, vb = rv.get(a), rv.get(b)
    if isinstance(va, float) and isinstance(vb, float):
        noise: float | NotEstimable = Z95 * math.sqrt((va + vb) / (n * k))
    else:
        noise = NotEstimable("only one trial per part: judge noise unknown")
        notes.append("judge noise unknown: grade each answer more than once to measure it")

    db = differential_bias(d, positive, a, b, n_boot=n_boot, seed=seed)
    row = None if isinstance(db, NotEstimable) else db.iloc[0]
    if row is None or isinstance(row["diff_bias"], NotEstimable):
        reason = db.reason if isinstance(db, NotEstimable) else row["diff_bias"].reason
        diff_bias = diff_bias_ci = bias_bound = NotEstimable(reason)
        notes.append("bias unknown: without a reference the MRD is a lower bound (noise only)")
    else:
        diff_bias = float(row["diff_bias"])
        diff_bias_ci = (float(row["ci_lo"]), float(row["ci_hi"]))
        bias_bound = max(abs(diff_bias_ci[0]), abs(diff_bias_ci[1]))
        notes.append(
            f"bias bound comes from {int(row['n_items'])} reference items; "
            "a larger reference set tightens it, more trials do not"
        )

    if isinstance(noise, float) and isinstance(bias_bound, float):
        total: float | NotEstimable = noise + bias_bound
    else:
        missing = [x.reason for x in (noise, bias_bound) if isinstance(x, NotEstimable)]
        total = NotEstimable("; ".join(missing))
    return MRDResult(
        judge, a, b, n, k, diff_observed, noise, bias_bound, total, diff_bias, diff_bias_ci, notes
    )
