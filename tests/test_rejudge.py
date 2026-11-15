import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rejudge", Path(__file__).parent.parent / "study/llm-chatbot/rejudge.py"
)
rejudge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rejudge)

PARTS = [(f"q{i}", s) for i in range(6) for s in ("v1", "v2")]


def test_plan_covers_every_part_and_trial_once():
    todo = rejudge.plan(PARTS, 3, set())
    assert len(todo) == 36 and len(set(todo)) == 36
    assert [t for _, _, t in todo] == sorted(t for _, _, t in todo)


def test_plan_order_is_seeded_and_differs_between_trials():
    a, b = rejudge.plan(PARTS, 2, set()), rejudge.plan(PARTS, 2, set())
    assert a == b
    assert [p[:2] for p in a[:12]] != [p[:2] for p in a[12:]]


def test_resume_skips_done_but_retries_errors(tmp_path):
    out = tmp_path / "t.jsonl"
    rows = [
        {"item": "q0", "system": "v1", "trial": 0, "judge": "j", "arm": "A", "judge_error": None},
        {"item": "q1", "system": "v1", "trial": 0, "judge": "j", "arm": "A", "judge_error": "x"},
        {
            "item": "q2",
            "system": "v1",
            "trial": 0,
            "judge": "other",
            "arm": "A",
            "judge_error": None,
        },
        {"item": "q3", "system": "v1", "trial": 0, "judge": "j", "arm": "B", "judge_error": None},
    ]
    out.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    done = rejudge.done_keys(out, "j", "A")
    assert done == {("q0", "v1", 0)}
    assert len(rejudge.plan(PARTS, 3, done)) == 35
    assert rejudge.done_keys(tmp_path / "missing.jsonl", "j", "A") == set()


def test_permutation_is_seeded_complete_and_varies():
    p = rejudge.permutation("q1", 0, 4)
    assert sorted(p) == [0, 1, 2, 3]
    assert p == rejudge.permutation("q1", 0, 4)
    assert len({tuple(rejudge.permutation("q1", t, 4)) for t in range(5)}) > 1


def test_arms_match_protocol():
    assert rejudge.ARMS["A"]["seeds"] == [0, 1, 2] and rejudge.ARMS["A"]["temperature"] == 0.0
    assert rejudge.ARMS["B"]["seeds"] == [1, 2, 3, 4, 5] and rejudge.ARMS["B"]["temperature"] == 0.7
    assert rejudge.ARMS["C"]["shuffle"] and rejudge.ARMS["C"]["reference_only"]
