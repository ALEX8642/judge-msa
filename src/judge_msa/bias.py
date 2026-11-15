"""Judge scores against a reference, by group, and the difference in bias between two systems."""

from __future__ import annotations

import numpy as np
import pandas as pd

from judge_msa.bootstrap import DEFAULT_N_BOOT, bootstrap_items
from judge_msa.table import PART, NotEstimable


def part_means(df: pd.DataFrame, positive: str) -> pd.DataFrame:
    """One row per (item, system, judge): share of trials with the positive verdict, and r.

    An optional ``weight`` column (constant within a part) carries sampling weights for the
    reference parts, for when the reference sample was not drawn at random from all parts.
    """
    d = df.assign(y=(df["verdict"] == positive).astype(float))
    if "weight" not in d.columns:
        d = d.assign(weight=1.0)
    out = d.groupby(PART + ["judge"], sort=False).agg(
        ybar=("y", "mean"), k=("y", "size"), reference=("reference", "first"), w=("weight", "first")
    )
    out = out.reset_index()
    out["r"] = np.where(
        out["reference"].notna(), (out["reference"] == positive).astype(float), np.nan
    )
    return out


def _strata(parts: pd.DataFrame, items: pd.Index) -> np.ndarray | None:
    """Items that share a sampling weight were sampled together: resample them together."""
    w = parts.groupby("item")["w"].first().reindex(items).to_numpy()
    return w if len(np.unique(w)) > 1 else None


class _ItemSums:
    """Per-item sums for a subset of parts, aligned to a shared item index, for fast resampling."""

    def __init__(self, parts: pd.DataFrame, items: pd.Index, cols: list[str]):
        w = parts["w"] if "w" in parts.columns else pd.Series(1.0, index=parts.index)
        weighted = parts[cols].mul(w, axis=0).assign(item=parts["item"], w=w)
        g = weighted.groupby("item")
        self.n = g["w"].sum().reindex(items, fill_value=0.0).to_numpy(dtype=float)
        self.sums = {c: g[c].sum().reindex(items, fill_value=0.0).to_numpy() for c in cols}

    def mean(self, col: str, idx: np.ndarray | slice = slice(None)) -> float:
        n = self.n[idx].sum()
        return float(self.sums[col][idx].sum() / n) if n else float("nan")


def bias_table(
    df: pd.DataFrame,
    positive: str,
    by: str = "system",
    *,
    n_boot: int = DEFAULT_N_BOOT,
    seed: int = 0,
) -> pd.DataFrame | NotEstimable:
    """Judge score minus reference score, per judge and group, on parts that have a reference."""
    pm = part_means(df, positive)
    if by not in PART + ["judge"]:
        pm = pm.merge(df[PART + [by]].drop_duplicates(PART), on=PART, how="left")
    pm = pm[pm["r"].notna()]
    if pm.empty:
        return NotEstimable("no reference")
    pm = pm.assign(d=pm["ybar"] - pm["r"])
    items = pd.Index(pm["item"].unique())
    strata = _strata(pm, items)
    rows = []
    for (judge, group), g in pm.groupby(["judge", by], sort=True):
        s = _ItemSums(g, items, ["ybar", "r", "d"])
        lo, hi = bootstrap_items(
            len(items), lambda i, s=s: s.mean("d", i), n_boot=n_boot, seed=seed
        )
        rows.append(
            {
                "judge": judge,
                by: group,
                "n_parts": len(g),
                "judge_score": s.mean("ybar"),
                "ref_score": s.mean("r"),
                "bias": s.mean("d"),
                "ci_lo": lo,
                "ci_hi": hi,
            }
        )
    return pd.DataFrame(rows)


def differential_bias(
    df: pd.DataFrame,
    positive: str,
    a: str,
    b: str,
    *,
    n_boot: int = DEFAULT_N_BOOT,
    seed: int = 0,
) -> pd.DataFrame | NotEstimable:
    """bias(system a) - bias(system b) per judge. This is what distorts an a-versus-b comparison."""
    pm = part_means(df, positive)
    pm = pm[pm["r"].notna() & pm["system"].isin([a, b])]
    if pm.empty:
        return NotEstimable("no reference")
    pm = pm.assign(d=pm["ybar"] - pm["r"])
    items = pd.Index(pm["item"].unique())
    strata = _strata(pm, items)
    rows = []
    for judge, g in pm.groupby("judge", sort=True):
        sa = _ItemSums(g[g["system"] == a], items, ["d"])
        sb = _ItemSums(g[g["system"] == b], items, ["d"])
        if not sa.n.sum() or not sb.n.sum():
            ne = NotEstimable(f"no reference for both {a} and {b}")
            rows.append({"judge": judge, "diff_bias": ne, "ci_lo": ne, "ci_hi": ne, "n_items": 0})
            continue

        def stat(i, sa=sa, sb=sb):
            return sa.mean("d", i) - sb.mean("d", i)

        lo, hi = bootstrap_items(len(items), stat, n_boot=n_boot, seed=seed, strata=strata)
        rows.append(
            {
                "judge": judge,
                "diff_bias": stat(slice(None)),
                "ci_lo": lo,
                "ci_hi": hi,
                "n_items": int(((sa.n > 0) | (sb.n > 0)).sum()),
            }
        )
    return pd.DataFrame(rows).astype({"diff_bias": object, "ci_lo": object, "ci_hi": object})


def difference_by_judge(
    df: pd.DataFrame,
    positive: str,
    a: str,
    b: str,
    *,
    n_boot: int = DEFAULT_N_BOOT,
    seed: int = 0,
) -> pd.DataFrame:
    """score(a) - score(b) as each judge sees it, on all parts. ``attrs['spread']`` = max - min.

    Sampling weights describe how the reference parts were drawn, so they are not used here.
    """
    pm = part_means(df, positive).assign(w=1.0)
    pm = pm[pm["system"].isin([a, b])]
    items = pd.Index(pm["item"].unique())
    rows = []
    for judge, g in pm.groupby("judge", sort=True):
        sa = _ItemSums(g[g["system"] == a], items, ["ybar"])
        sb = _ItemSums(g[g["system"] == b], items, ["ybar"])

        def stat(i, sa=sa, sb=sb):
            return sa.mean("ybar", i) - sb.mean("ybar", i)

        lo, hi = bootstrap_items(len(items), stat, n_boot=n_boot, seed=seed)
        rows.append(
            {
                "judge": judge,
                "score_a": sa.mean("ybar"),
                "score_b": sb.mean("ybar"),
                "diff": stat(slice(None)),
                "ci_lo": lo,
                "ci_hi": hi,
            }
        )
    out = pd.DataFrame(rows)
    out.attrs["spread"] = float(out["diff"].max() - out["diff"].min()) if len(out) > 1 else 0.0
    return out
