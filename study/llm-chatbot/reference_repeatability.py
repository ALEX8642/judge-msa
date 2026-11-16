"""How repeatable is the human reference? The grader's first session against his blind regrade.

    python reference_repeatability.py --llm-chatbot PATH

Writes data/reference-repeat.csv (the grader as a judge with two trials on the 30 regraded answers)
and prints agreement on the pass/fail verdict and on the raw grade.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from build_table import human_pass, pf

from judge_msa.agreement import cohen_kappa, within_judge
from judge_msa.table import validate

HERE = Path(__file__).parent


def lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-chatbot", required=True, type=Path)
    root = ap.parse_args().llm_chatbot.expanduser()
    category = {i["id"]: i["category"] for i in lines(root / "evals/test.jsonl")}
    key1 = json.loads((root / "evals/sessions/blind_key.json").read_text())["screens"]
    first = {
        (key1[g["code"]]["item"], key1[g["code"]]["system"]): g
        for g in lines(root / "evals/sessions/blind_grades.jsonl")
    }
    key2 = json.loads((HERE / "data/regrade_key.json").read_text())["screens"]
    rows = []
    for g in lines(HERE / "data/regrade_grades.jsonl"):
        part = (key2[g["code"]]["item"], key2[g["code"]]["system"])
        for trial, grade in enumerate((first[part], g)):
            rows.append(
                {
                    "item": part[0],
                    "system": part[1],
                    "judge": "human",
                    "trial": trial,
                    "verdict": pf(human_pass(grade, category[part[0]])),
                    "raw": grade["correct"] + ("/" + grade["support"] if grade["support"] else ""),
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "data/reference-repeat.csv", index=False)
    w = within_judge(validate(df)).iloc[0]
    wide = df.pivot(index=["item", "system"], columns="trial", values=["verdict", "raw"])
    same = wide["verdict"][0] == wide["verdict"][1]
    print(f"answers regraded: {len(wide)}")
    print(
        f"same pass/fail verdict: {int(same.sum())} of {len(wide)}; kappa {w['fleiss_kappa']:.3f}"
    )
    print("by system:", same.groupby(level="system").agg(["sum", "size"]).to_dict("index"))
    print(
        pd.crosstab(wide["verdict"][0], wide["verdict"][1], rownames=["first"], colnames=["second"])
    )
    raw_same = wide["raw"][0] == wide["raw"][1]
    print(
        f"same raw grade: {int(raw_same.sum())} of {len(wide)}; "
        f"kappa {cohen_kappa(wide['raw'][0], wide['raw'][1]):.3f}"
    )
    changed = wide[~raw_same]
    print(changed.to_string())


if __name__ == "__main__":
    main()
