"""Turn LLM-chatbot's committed results, and this study's trial files, into verdict tables.

    python build_table.py --llm-chatbot ~/LLM-chatbot            # data/existing.csv
    python build_table.py --llm-chatbot ~/LLM-chatbot --arm A    # data/arm-A.csv

Columns: item, system, judge, trial, verdict (pass/fail on "correct and supported"), correct
(pass/fail on correctness alone), reference, weight, category, manual, selected.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
SYSTEMS = ("v1", "v2")
EXISTING_JUDGES = {"phi4": "phi4:14b", "mistral": "mistral-small3.2:24b"}
N_TEST = 169


def pf(value) -> str | None:
    return None if value is None else ("pass" if value else "fail")


def human_pass(grade: dict, category: str) -> bool:
    """As LLM-chatbot scored its blind session (reproduces its 42 and 31 of 50): an answerable
    question passes when graded correct with the cited pages showing it; an unanswerable one passes
    only when the answer declined."""
    if category == "unanswerable":
        return grade["correct"] == "declined"
    return grade["correct"] == "correct" and grade["support"] == "yes"


def reference(root: Path, categories: dict[str, str]) -> pd.DataFrame:
    """One row per blind-graded answer: reference verdict and sampling weight."""
    key = json.loads((root / "evals/sessions/blind_key.json").read_text())
    grades = [
        json.loads(line)
        for line in (root / "evals/sessions/blind_grades.jsonl").read_text().splitlines()
        if line.strip()
    ]
    selected = {i for ids in key["groups"].values() for i in ids}
    n_random = len(set(key["items"]) - selected)
    w_random = (N_TEST - len(selected)) / n_random
    rows = []
    for g in grades:
        screen = key["screens"][g["code"]]
        item = screen["item"]
        rows.append(
            {
                "item": item,
                "system": screen["system"],
                "reference": pf(human_pass(g, categories[item])),
                "weight": 1.0 if item in selected else w_random,
                "selected": item in selected,
            }
        )
    return pd.DataFrame(rows)


def existing(root: Path) -> pd.DataFrame:
    rows = []
    for system in SYSTEMS:
        for short, judge in EXISTING_JUDGES.items():
            path = root / "evals/results/test" / f"{system}-test-{short}.json"
            for g in json.loads(path.read_text())["repeats"][0]["items"]:
                rows.append(
                    {
                        "item": g["id"],
                        "system": system,
                        "judge": judge,
                        "trial": 0,
                        "verdict": pf(g["primary"]),
                        "correct": pf(g["correct"]),
                        "category": g["category"],
                        "manual": g["manual"],
                    }
                )
    return pd.DataFrame(rows)


def arm(name: str, meta: pd.DataFrame) -> pd.DataFrame:
    recs = [
        json.loads(line)
        for line in (HERE / "data" / f"trials-{name}.jsonl").read_text().splitlines()
        if line.strip()
    ]
    df = pd.DataFrame(recs)
    df = df[df["judge_error"].isna()].drop_duplicates(
        ["item", "system", "judge", "trial"], keep="last"
    )
    df["verdict"] = df["primary"].map(pf)
    df["correct"] = df["correct"].map(pf)
    cols = ["item", "system", "judge", "trial", "verdict", "correct", "seconds"]
    return df[cols].merge(meta, on="item", how="left")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-chatbot", required=True, type=Path)
    ap.add_argument("--arm", help="build data/arm-<ARM>.csv from data/trials-<ARM>.jsonl instead")
    args = ap.parse_args()
    root = args.llm_chatbot.expanduser()

    table = existing(root)
    meta = table.drop_duplicates("item")[["item", "category", "manual"]]
    ref = reference(root, dict(zip(meta["item"], meta["category"], strict=True)))
    if args.arm:
        table = arm(args.arm, meta)
    table = table.merge(ref, on=["item", "system"], how="left")
    table["weight"] = table["weight"].fillna(1.0)
    table["selected"] = table["selected"].fillna(False)
    out = HERE / "data" / (f"arm-{args.arm}.csv" if args.arm else "existing.csv")
    table.sort_values(["item", "system", "judge", "trial"]).to_csv(out, index=False)
    print(
        f"wrote {out}: {len(table)} rows, {table['verdict'].isna().sum()} without a verdict, "
        f"{table.drop_duplicates(['item', 'system'])['reference'].notna().sum()} with a reference"
    )


if __name__ == "__main__":
    main()
