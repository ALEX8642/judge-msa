"""Attribute agreement statistics: within judge, between judges, and against a reference."""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

from judge_msa.table import PART, NotEstimable

NO_VARIATION = "no variation: every verdict is the same"


def cohen_kappa(
    a: pd.Series, b: pd.Series, weights: pd.Series | None = None
) -> float | NotEstimable:
    """Cohen's kappa for two paired series of labels, optionally with a weight per pair."""
    a, b = a.reset_index(drop=True), b.reset_index(drop=True)
    if len(a) == 0:
        return NotEstimable("no paired verdicts")
    w = pd.Series(1.0, index=a.index) if weights is None else weights.reset_index(drop=True)
    w = w / w.sum()
    cats = sorted(set(a) | set(b))
    if len(cats) < 2:
        return NotEstimable(NO_VARIATION)
    po = float(w[a == b].sum())
    pa = w.groupby(a).sum().reindex(cats, fill_value=0.0)
    pb = w.groupby(b).sum().reindex(cats, fill_value=0.0)
    pe = float((pa * pb).sum())
    if pe >= 1.0:
        return NotEstimable(NO_VARIATION)
    return (po - pe) / (1 - pe)


def _subject_agreement(counts: np.ndarray) -> np.ndarray:
    """Share of agreeing rating pairs per subject; NaN where a subject has fewer than 2 ratings."""
    n = counts.sum(axis=1).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n >= 2, (counts * (counts - 1)).sum(axis=1) / (n * (n - 1)), np.nan)


def fleiss_kappa(counts: np.ndarray) -> float | NotEstimable:
    """Fleiss' kappa from a subjects x categories count table.

    Subjects may have different numbers of ratings (those with fewer than 2 are skipped); with equal
    numbers this is the standard Fleiss statistic.
    """
    counts = np.asarray(counts, dtype=float)
    p_i = _subject_agreement(counts)
    used = ~np.isnan(p_i)
    if not used.any():
        return NotEstimable("needs at least 2 ratings per part")
    share = counts[used].sum(axis=0) / counts[used].sum()
    pe = float((share**2).sum())
    if pe >= 1.0:
        return NotEstimable(NO_VARIATION)
    return (float(p_i[used].mean()) - pe) / (1 - pe)


def _counts(df: pd.DataFrame, unit: list[str]) -> pd.DataFrame:
    return df.groupby(unit + ["verdict"]).size().unstack("verdict", fill_value=0)


def within_judge(df: pd.DataFrame) -> pd.DataFrame:
    """Repeatability per judge: do repeated trials of the same part agree?"""
    rows = []
    for judge, d in df.groupby("judge", sort=True):
        counts = _counts(d, PART)
        n_trials = int(counts.sum(axis=1).median())
        p_i = _subject_agreement(counts.to_numpy())
        used = ~np.isnan(p_i)
        row = {"judge": judge, "n_parts": len(counts), "n_trials": n_trials}
        if not used.any():
            ne = NotEstimable("only one trial per part")
            row |= {"pct_all_agree": ne, "flip_rate": ne, "fleiss_kappa": ne}
        else:
            row |= {
                "pct_all_agree": float((p_i[used] == 1).mean()),
                "flip_rate": float((1 - p_i[used]).mean()),
                "fleiss_kappa": fleiss_kappa(counts.to_numpy()),
            }
        rows.append(row)
    return pd.DataFrame(rows).astype(
        {"pct_all_agree": object, "flip_rate": object, "fleiss_kappa": object}
    )


def modal_verdicts(df: pd.DataFrame) -> pd.DataFrame:
    """One verdict per (part, judge): the most frequent over trials; ties go to the earliest.

    Returns a parts x judges table restricted to parts every judge graded.
    """
    g = df.groupby(PART + ["judge", "verdict"]).agg(n=("trial", "size"), first=("trial", "min"))
    g = g.reset_index().sort_values(["n", "first"], ascending=[False, True])
    modal = g.drop_duplicates(PART + ["judge"]).set_index(PART + ["judge"])["verdict"]
    return modal.unstack("judge").dropna()


def between_judges(df: pd.DataFrame) -> dict | NotEstimable:
    """Reproducibility: do different judges reach the same verdict on the same part?"""
    judges = sorted(df["judge"].unique())
    if len(judges) < 2:
        return NotEstimable("only one judge")
    modal = modal_verdicts(df)
    if modal.empty:
        return NotEstimable("no part was graded by every judge")
    pairs = [
        {
            "judge_a": a,
            "judge_b": b,
            "agreement": float((modal[a] == modal[b]).mean()),
            "cohen_kappa": cohen_kappa(modal[a], modal[b]),
        }
        for a, b in combinations(judges, 2)
    ]
    cats = sorted(pd.unique(modal.to_numpy().ravel()))
    counts = np.stack([(modal.to_numpy() == c).sum(axis=1) for c in cats], axis=1)
    common = df.set_index(PART).loc[modal.index]
    all_agree = common.groupby(level=PART)["verdict"].nunique() == 1
    return {
        "n_parts": len(modal),
        "pairwise": pd.DataFrame(pairs).astype({"cohen_kappa": object}),
        "fleiss_kappa": fleiss_kappa(counts),
        "pct_all_agree": float(all_agree.mean()),
    }


def _rate(num: float, den: float, what: str) -> float | NotEstimable:
    return num / den if den else NotEstimable(f"no parts where the reference is {what}")


def vs_reference(
    df: pd.DataFrame, positive: str, by: str | None = None
) -> pd.DataFrame | NotEstimable:
    """Each judge against the reference: agreement, kappa, miss rate and false-alarm rate.

    Miss = the judge passes an answer the reference fails. False alarm = the judge fails an answer
    the reference passes. Rates are over all trials, weighted by ``weight`` when that column exists.
    """
    d = df[df["reference"].notna()]
    if d.empty:
        return NotEstimable("no reference")
    keys = ["judge"] + ([by] if by else [])
    rows = []
    for key, g in d.groupby(keys, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        w = g["weight"].astype(float) if "weight" in g.columns else pd.Series(1.0, index=g.index)
        y = g["verdict"] == positive
        r = g["reference"] == positive
        rows.append(
            dict(zip(keys, key, strict=True))
            | {
                "n_parts": int(g[PART].drop_duplicates().shape[0]),
                "agreement": float(w[g["verdict"] == g["reference"]].sum() / w.sum()),
                "cohen_kappa": cohen_kappa(g["verdict"], g["reference"], w),
                "miss_rate": _rate(float(w[y & ~r].sum()), float(w[~r].sum()), "negative"),
                "false_alarm_rate": _rate(float(w[~y & r].sum()), float(w[r].sum()), "positive"),
            }
        )
    cols = {c: object for c in ("cohen_kappa", "miss_rate", "false_alarm_rate")}
    return pd.DataFrame(rows).astype(cols)
