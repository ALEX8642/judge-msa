"""Load and validate a long table of judge verdicts.

Canonical columns: item, system, judge, trial, verdict, reference. A *part* is (item, system).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CANONICAL = ["item", "system", "judge", "trial", "verdict", "reference"]
KEY = ["item", "system", "judge", "trial"]
PART = ["item", "system"]
NO_SYSTEM = "_"


class TableError(ValueError):
    """The verdict table cannot be analysed as given."""


@dataclass(frozen=True)
class NotEstimable:
    """Returned in place of a statistic the data cannot support."""

    reason: str

    def __str__(self) -> str:
        return f"not estimable: {self.reason}"


def _read(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".jsonl", ".ndjson"}:
        return pd.read_json(path, lines=True)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise TableError(f"unsupported file type {suffix!r}: use .csv, .jsonl or .parquet")


def load_table(
    path: str | Path,
    *,
    item: str = "item",
    judge: str = "judge",
    trial: str | None = "trial",
    verdict: str = "verdict",
    system: str | None = None,
    reference: str | None = None,
    by: Iterable[str] = (),
) -> pd.DataFrame:
    """Read a CSV / JSONL / Parquet file and return a validated canonical table."""
    raw = _read(Path(path))
    wanted = {"item": item, "judge": judge, "verdict": verdict}
    if system:
        wanted["system"] = system
    if reference:
        wanted["reference"] = reference
    if trial and trial in raw.columns:
        wanted["trial"] = trial
    missing = [
        f"{canon} (column {src!r})" for canon, src in wanted.items() if src not in raw.columns
    ]
    by = [b for b in by if b]
    missing += [f"by column {b!r}" for b in by if b not in raw.columns]
    if missing:
        raise TableError("missing columns: " + ", ".join(missing))
    out = pd.DataFrame({canon: raw[src] for canon, src in wanted.items()})
    for b in by:
        if b not in out.columns:
            out[b] = raw[b]
    return validate(out)


def _as_str(col: pd.Series) -> pd.Series:
    return col.map(lambda v: v if pd.isna(v) else str(v)).astype("object")


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Canonical dtypes; drop rows without a verdict (counted in ``attrs['dropped']``)."""
    for col in ("item", "judge", "verdict"):
        if col not in df.columns:
            raise TableError(f"missing columns: {col}")
    out = df.copy()
    if "system" not in out.columns:
        out["system"] = NO_SYSTEM
    if "trial" not in out.columns:
        out["trial"] = 0
    if "reference" not in out.columns:
        out["reference"] = pd.NA
    extras = [c for c in out.columns if c not in CANONICAL]
    out = out[CANONICAL + extras]

    for col in ("item", "system", "judge"):
        if out[col].isna().any():
            raise TableError(f"column {col!r} has missing values")
        out[col] = out[col].astype(str)
    out["verdict"] = _as_str(out["verdict"])
    out["reference"] = _as_str(out["reference"])
    try:
        out["trial"] = out["trial"].astype(int)
    except (TypeError, ValueError) as e:
        raise TableError("column 'trial' must hold integers") from e

    dup = out[out.duplicated(KEY, keep=False)]
    if len(dup):
        keys = dup[KEY].drop_duplicates().head(5).to_dict("records")
        raise TableError(f"duplicate rows for (item, system, judge, trial): {keys}")

    refs = out.dropna(subset=["reference"]).groupby(PART)["reference"].nunique()
    bad = refs[refs > 1]
    if len(bad):
        raise TableError(f"reference differs within a part (item, system): {list(bad.index[:5])}")
    # a reference given on some rows of a part applies to the whole part
    out["reference"] = out.groupby(PART)["reference"].transform(
        lambda s: s.dropna().iloc[0] if s.notna().any() else pd.NA
    )

    dropped = int(out["verdict"].isna().sum())
    out = out[out["verdict"].notna()].reset_index(drop=True)
    out.attrs["dropped"] = dropped
    return out
