"""Same judge, same answers, temperature 0: do two setups give the same verdicts?

Compares the existing laptop grades with arm A's first trial (5090, 16,384-token context) and,
when present, arm D (5090, 4,096-token context). Prints agreement overall and for answers whose
cited source is long. Run from this directory: python compare_setups.py --llm-chatbot PATH
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
KEY = ["item", "system", "judge"]
LONG_CHARS = 12000  # about 3,000 tokens


def load(name: str) -> pd.DataFrame | None:
    p = HERE / "data" / name
    if not p.exists():
        return None
    df = pd.read_csv(p)
    if "trial" in df.columns:
        df = df[df["trial"] == 0]
    return df.dropna(subset=["verdict"]).set_index(KEY)["verdict"]


def source_lengths(root: Path) -> pd.Series:
    """Length in characters of each answer's cited text, as LLM-chatbot's grader builds it."""
    import sys

    sys.path.insert(0, str(root))
    from evals.grade import cited_source
    from evals.items import load_items
    from manualqa.blocks import load_pages

    items = {i.id: i for i in load_items(root / "evals/test.jsonl")}
    blocks, pages = {}, {}
    for pp in load_pages(root / "data/ingest/composed.jsonl"):
        pages[(pp.manual, pp.page)] = "\n".join(b.text for b in pp.blocks)
        blocks.update({b.id: b.text for b in pp.blocks})
    rows = {}
    for system in ("v1", "v2"):
        raw = json.loads((root / f"evals/results/raw/{system}-test.json").read_text())
        for o in raw["repeats"][0]:
            rows[(o["id"], system)] = len(
                cited_source(o, items[o["id"]].manual, blocks, pages) or ""
            )
    return pd.Series(rows).rename_axis(["item", "system"]).rename("source_chars")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-chatbot", required=True, type=Path)
    args = ap.parse_args()
    lengths = source_lengths(args.llm_chatbot.expanduser())
    setups = {
        "laptop (existing)": load("existing.csv"),
        "5090, 16k context (arm A)": load("arm-A.csv"),
        "5090, 4k context (arm D)": load("arm-D.csv"),
    }
    setups = {k: v for k, v in setups.items() if v is not None}
    names = list(setups)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            both = pd.concat([setups[a].rename("a"), setups[b].rename("b")], axis=1, join="inner")
            both = both.join(lengths, on=["item", "system"]).reset_index()
            both["long"] = both["source_chars"] > LONG_CHARS
            for (judge, system, long), g in both.groupby(["judge", "system", "long"]):
                rows.append(
                    {
                        "setup_a": a,
                        "setup_b": b,
                        "judge": judge,
                        "system": system,
                        "long_source": bool(long),
                        "answers": len(g),
                        "same_verdict": int((g["a"] == g["b"]).sum()),
                        "pass_a": int((g["a"] == "pass").sum()),
                        "pass_b": int((g["b"] == "pass").sum()),
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "reports" / "setups.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
