"""Variance components of a binary verdict on the score scale (0-1), by the method of moments."""

from __future__ import annotations

import numpy as np
import pandas as pd

from judge_msa.table import PART, NotEstimable

ONE_TRIAL = "only one trial per part"


def _part_stats(df: pd.DataFrame, positive: str) -> pd.DataFrame:
    d = df.assign(y=(df["verdict"] == positive).astype(float))
    g = d.groupby(PART + ["judge"], sort=False)["y"]
    out = g.agg(m="mean", k="size", v=lambda s: s.var(ddof=1) if len(s) > 1 else np.nan)
    return out.reset_index()


def repeatability_var(df: pd.DataFrame, positive: str) -> pd.DataFrame:
    """Mean trial-to-trial variance of the verdict within a part, per judge and system."""
    ps = _part_stats(df, positive)
    rows = []
    for (judge, system), g in ps.groupby(["judge", "system"], sort=True):
        used = g["v"].notna()
        rows.append(
            {
                "judge": judge,
                "system": system,
                "v": float(g.loc[used, "v"].mean()) if used.any() else NotEstimable(ONE_TRIAL),
                "n_parts_used": int(used.sum()),
            }
        )
    return pd.DataFrame(rows).astype({"v": object})


def components(df: pd.DataFrame, positive: str) -> pd.DataFrame:
    """Split verdict variance into part, judge, judge-by-part and repeatability.

    Uses parts graded by every judge. ``attrs['grr_share']`` is the share of variance that comes
    from the measurement system (everything except the parts themselves).
    """
    ps = _part_stats(df, positive)
    m = ps.pivot(index=PART, columns="judge", values="m").dropna()
    k = ps.pivot(index=PART, columns="judge", values="k").loc[m.index]
    v = ps.pivot(index=PART, columns="judge", values="v").loc[m.index]
    n_judges = m.shape[1]
    k_bar = float(k.to_numpy().mean())

    has_rep = bool(v.notna().to_numpy().any())
    rep = float(np.nanmean(v.to_numpy())) if has_rep else 0.0
    if n_judges > 1:
        judge_var = float(m.mean(axis=0).var(ddof=1))
        centred = m - m.mean(axis=0)
        jxp = max(float(centred.var(axis=1, ddof=1).mean()) - rep / k_bar, 0.0)
    else:
        judge_var = jxp = 0.0
    part = max(float(m.mean(axis=1).var(ddof=1)) - (jxp + rep / k_bar) / n_judges, 0.0)

    one_judge = NotEstimable("only one judge")
    rows = [
        ("part", part),
        ("judge", judge_var if n_judges > 1 else one_judge),
        ("judge_x_part", jxp if n_judges > 1 else one_judge),
        ("repeatability", rep if has_rep else NotEstimable(ONE_TRIAL)),
    ]
    total = sum(x for _, x in rows if isinstance(x, float))
    out = pd.DataFrame(
        [
            {
                "component": name,
                "variance": x,
                "share": (x / total if total else 0.0) if isinstance(x, float) else x,
            }
            for name, x in rows
        ]
    ).astype({"variance": object, "share": object})
    out.attrs["grr_share"] = (total - part) / total if total else NotEstimable("no variation")
    out.attrs["n_parts"] = len(m)
    return out
