"""Re-judge fixed LLM-chatbot answers several times, for the repeatability arms of the study.

Run with LLM-chatbot importable (it supplies the grader, the prompts and the judge client):

    python rejudge.py --llm-chatbot ~/LLM-chatbot --arm A --judge phi4:14b \\
        --base-url http://localhost:11434/v1 --out data/trials-A.jsonl

Arms (see protocol.md): A = temperature 0, seeds 0-2, all answers. B = temperature 0.7, seeds 1-5,
all answers. C = temperature 0, seed 0, key facts listed in 5 seeded random orders, reference
answers with at least 2 key facts. The output is append-only JSON lines and the run is resumable:
gradings already in the file are skipped.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import random
import sys
import time
from pathlib import Path

SYSTEMS = ("v1", "v2")
ARMS = {
    "A": {"temperature": 0.0, "seeds": [0, 1, 2], "shuffle": False, "reference_only": False},
    "B": {"temperature": 0.7, "seeds": [1, 2, 3, 4, 5], "shuffle": False, "reference_only": False},
    "C": {"temperature": 0.0, "seeds": [0] * 5, "shuffle": True, "reference_only": True},
}
ORDER_SEED = 20261115


def done_keys(path: Path, judge: str, arm: str) -> set[tuple[str, str, int]]:
    """(item, system, trial) already graded without a judge error for this judge and arm."""
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["judge"] == judge and r["arm"] == arm and not r["judge_error"]:
            out.add((r["item"], r["system"], r["trial"]))
    return out


def permutation(item: str, trial: int, n: int) -> list[int]:
    """Seeded order of n key facts for arm C; the same for every judge and system."""
    order = list(range(n))
    random.Random(f"{ORDER_SEED}:{item}:{trial}").shuffle(order)
    return order


def plan(parts: list[tuple[str, str]], n_trials: int, done: set) -> list[tuple[str, str, int]]:
    """Gradings still to do: trial by trial, parts in a seeded random order within each trial."""
    todo = []
    for trial in range(n_trials):
        order = sorted(parts)
        random.Random(f"{ORDER_SEED}:order:{trial}").shuffle(order)
        todo += [(i, s, trial) for i, s in order if (i, s, trial) not in done]
    return todo


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-chatbot", required=True, type=Path)
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--judge", required=True)
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, help="stop after this many gradings (timing probe)")
    args = ap.parse_args()
    arm = ARMS[args.arm]

    root = args.llm_chatbot.expanduser().resolve()
    sys.path.insert(0, str(root))
    import requests
    from evals.grade import cited_source, grade_item, page_source
    from evals.items import load_items
    from evals.run_eval import Judge, first_json_object
    from manualqa.blocks import load_pages

    class TrialJudge(Judge):
        """LLM-chatbot's judge client with the temperature and seed set per trial, no caching."""

        temperature = 0.0
        max_tokens_override = 1500  # as in LLM-chatbot's scoring run

        def ask(self, prompt: str) -> dict:
            body = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "seed": self.seed,
                "max_tokens": self.max_tokens_override,
            }
            last = ""
            for wait in (0, 10, 30, 60, 120, 300):
                time.sleep(wait)
                try:
                    r = requests.post(self.url, json=body, headers=self.headers, timeout=300)
                    r.raise_for_status()
                except requests.RequestException as e:
                    last = repr(e)
                    continue
                last = r.json()["choices"][0]["message"]["content"] or ""
                parsed = first_json_object(last)
                if parsed is not None:
                    return parsed
            raise ValueError(f"judge returned no JSON: {last[:200]!r}")

    items = {i.id: i for i in load_items(root / "evals" / "test.jsonl")}
    answers = {
        s: {
            o["id"]: o
            for o in json.loads((root / "evals/results/raw" / f"{s}-test.json").read_text())[
                "repeats"
            ][0]
        }
        for s in SYSTEMS
    }
    blocks, pages = {}, {}
    for pp in load_pages(root / "data/ingest/composed.jsonl"):
        pages[(pp.manual, pp.page)] = "\n".join(b.text for b in pp.blocks)
        blocks.update({b.id: b.text for b in pp.blocks})

    parts = [(i, s) for s in SYSTEMS for i in answers[s]]
    if arm["reference_only"]:
        key = json.loads((root / "evals/sessions/blind_key.json").read_text())
        ref = {(v["item"], v["system"]) for v in key["screens"].values()}
        parts = [p for p in parts if p in ref and len(items[p[0]].key_facts) >= 2]
    todo = plan(parts, len(arm["seeds"]), done_keys(args.out, args.judge, args.arm))
    if args.limit:
        todo = todo[: args.limit]
    print(f"arm {args.arm} judge {args.judge}: {len(todo)} gradings to do", flush=True)

    judge = TrialJudge(args.base_url, "", args.judge)
    judge.temperature = arm["temperature"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a") as f:
        for n, (item_id, system, trial) in enumerate(todo, 1):
            item, out = items[item_id], answers[system][item_id]
            perm = None
            if arm["shuffle"]:
                perm = permutation(item_id, trial, len(item.key_facts))
                item = dataclasses.replace(item, key_facts=[item.key_facts[i] for i in perm])
            judge.seed = arm["seeds"][trial]
            source = cited_source(out, item.manual, blocks, pages)
            pages_only = page_source(out, item.manual, pages) if out.get("claims") else None
            t0 = time.time()
            g = grade_item(item, {**out, "cited_source": source, "page_source": pages_only}, judge)
            rec = {
                "item": item_id,
                "system": system,
                "judge": args.judge,
                "arm": args.arm,
                "trial": trial,
                "seed": judge.seed,
                "temperature": judge.temperature,
                "perm": perm,
                "primary": g["primary"],
                "correct": g["correct"],
                "abstained": g["abstained"],
                "supported_in_source": g["supported_in_source"],
                "facts_present": [bool(x.get("present")) for x in g["facts"]],
                "judge_error": g["judge_error"],
                "category": g["category"],
                "seconds": round(time.time() - t0, 2),
            }
            f.write(json.dumps(rec) + "\n")
            f.flush()
            if n % 25 == 0 or n == len(todo):
                print(f"{n}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
