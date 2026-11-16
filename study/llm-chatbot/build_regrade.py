"""Build the blind regrade session: 30 of the 100 reference answers, graded a second time.

Stratified by system and by the first verdict (per system: 9 first-pass answers and 6 first-fail
ones), seeded, with new random codes and a fresh shuffle, so nothing links a screen to the first
session. Uses LLM-chatbot's own grading sheet. Run with LLM-chatbot importable:

    python build_regrade.py --llm-chatbot ~/LLM-chatbot OUT_DIR KEY_FILE

Keep KEY_FILE away from the grader until the session is over.
"""

from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
from pathlib import Path

SEED = 20261115
PER_SYSTEM = {"pass": 9, "fail": 6}
MAX_PAGES = 4
SHORT = {"FAA": "FAA handbook", "Army_5kW_Generator_Operator": "Operator manual"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-chatbot", required=True, type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("key_file", type=Path)
    args = ap.parse_args()
    root = args.llm_chatbot.expanduser().resolve()
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).parent))
    import pymupdf
    from build_table import human_pass
    from evals.items import load_items
    from manualqa.geometry import render_page

    items = {i.id: i for i in load_items(root / "evals/test.jsonl")}
    key = json.loads((root / "evals/sessions/blind_key.json").read_text())
    first = {}
    for line in (root / "evals/sessions/blind_grades.jsonl").read_text().splitlines():
        g = json.loads(line)
        s = key["screens"][g["code"]]
        verdict = "pass" if human_pass(g, items[s["item"]].category) else "fail"
        first[(s["item"], s["system"])] = verdict
    answers = {
        s: {
            o["id"]: o
            for o in json.loads((root / f"evals/results/raw/{s}-test.json").read_text())["repeats"][
                0
            ]
        }
        for s in ("v1", "v2")
    }

    rng = random.Random(SEED)
    chosen = []
    for system in ("v1", "v2"):
        for verdict, n in PER_SYSTEM.items():
            pool = sorted(k for k, v in first.items() if k[1] == system and v == verdict)
            chosen += rng.sample(pool, n)

    (args.out / "pages").mkdir(parents=True, exist_ok=True)
    docs, rendered, screens, new_key = {}, set(), [], {}
    for item_id, system in chosen:
        it, out_ = items[item_id], answers[system][item_id]
        pages = []
        for n in list(dict.fromkeys(out_.get("cited_pages") or []))[:MAX_PAGES]:
            name = f"pages/{Path(it.manual).stem}-p{n:03d}.jpg"
            if name not in rendered:
                doc = docs.setdefault(it.manual, pymupdf.open(root / "manuals" / it.manual))
                render_page(doc[n - 1])[0].convert("RGB").save(args.out / name, quality=70)
                rendered.add(name)
            pages.append({"page": n, "src": name})
        code = secrets.token_hex(4)
        new_key[code] = {
            "item": item_id,
            "system": system,
            "first_verdict": first[(item_id, system)],
        }
        screens.append(
            {
                "code": code,
                "item": item_id,
                "question": it.question,
                "unanswerable": it.category == "unanswerable",
                "reference_answer": it.reference_answer,
                "key_facts": it.key_facts,
                "answer": out_["answer"].strip(),
                "manual": next(
                    (v for k, v in SHORT.items() if it.manual.startswith(k)), "Parts manual"
                ),
                "pages": pages,
            }
        )
    random.Random(SEED + 1).shuffle(screens)
    args.key_file.write_text(json.dumps({"seed": SEED, "screens": new_key}, indent=1) + "\n")
    html = (root / "evals/sessions/blind/template.html").read_text()
    html = html.replace("<title>Blind Answer Grading</title>", "<title>Blind Regrade</title>")
    html = html.replace("/*SCREENS*/[]", json.dumps(screens, ensure_ascii=False))
    (args.out / "index.html").write_text(html)
    print(len(screens), "screens,", len(rendered), "pages")


if __name__ == "__main__":
    main()
