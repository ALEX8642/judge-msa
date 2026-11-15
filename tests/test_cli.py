import json
import subprocess
import sys

import pandas as pd
import pytest

from judge_msa.simulate import JudgeSpec, simulate

SPEC = JudgeSpec(flip=0.05, miss={"A": 0.3, "B": 0.05})


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "judge_msa.cli", *args], capture_output=True, text=True
    )


def table(tmp_path, df, name="t.csv"):
    p = tmp_path / name
    df.to_csv(p, index=False)
    return str(p)


def analyze(tmp_path, df, *extra):
    out = tmp_path / "out"
    r = run(
        "analyze",
        table(tmp_path, df),
        "--system",
        "system",
        "--reference",
        "reference",
        "--out",
        str(out),
        "--n-boot",
        "100",
        *extra,
    )
    return r, out


@pytest.fixture(scope="module")
def full():
    return simulate(150, {"A": 0.7, "B": 0.6}, {"j": SPEC, "k": JudgeSpec(flip=0.1)}, 3, seed=0)


def test_writes_three_outputs_and_headline(tmp_path, full):
    r, out = analyze(tmp_path, full, "--positive", "pass", "--compare", "A", "B")
    assert r.returncode == 0, r.stderr
    result = json.loads((out / "result.json").read_text())
    assert len(result["mrd"]) == 2
    assert isinstance(result["mrd"][0]["mrd"], float)
    md = (out / "report.md").read_text()
    assert "can resolve differences above" in md
    assert "j reports A − B" in md
    html = (out / "report.html").read_text()
    assert "<svg" in html and "<table>" in html


def test_html_is_self_contained(tmp_path, full):
    _, out = analyze(tmp_path, full, "--positive", "pass")
    html = (out / "report.html").read_text()
    assert "http://" not in html and "https://" not in html
    assert "<script" not in html


def test_one_trial_reports_not_estimable(tmp_path, full):
    r, out = analyze(tmp_path, full[full["trial"] == 0], "--positive", "pass")
    assert r.returncode == 0, r.stderr
    md = (out / "report.md").read_text()
    assert "only one trial per part" in md
    assert "grade each answer more than once" in md


def test_no_reference_reports_not_estimable(tmp_path, full):
    out = tmp_path / "out"
    p = table(tmp_path, full.drop(columns="reference"))
    r = run(
        "analyze",
        p,
        "--system",
        "system",
        "--out",
        str(out),
        "--positive",
        "pass",
        "--n-boot",
        "50",
    )
    assert r.returncode == 0, r.stderr
    md = (out / "report.md").read_text()
    assert "no reference" in md
    assert "judges that agree may share the same bias" in md


def test_single_judge(tmp_path, full):
    r, out = analyze(tmp_path, full[full["judge"] == "j"], "--positive", "pass")
    assert r.returncode == 0, r.stderr
    assert "only one judge" in (out / "report.md").read_text()


def test_dropped_rows_are_reported(tmp_path, full):
    df = full.copy()
    df.loc[df.index[:7], "verdict"] = None
    r, out = analyze(tmp_path, df, "--positive", "pass")
    assert r.returncode == 0, r.stderr
    assert "7 rows had no verdict and were left out" in (out / "report.md").read_text()


def test_two_values_without_positive_asks(tmp_path, full):
    r, _ = analyze(tmp_path, full)
    assert r.returncode == 2
    assert "--positive" in r.stderr and "fail" in r.stderr


def test_three_values_without_positive_still_reports_agreement(tmp_path, full):
    df = full.copy()
    df.loc[df.index[::9], "verdict"] = "declined"
    r, out = analyze(tmp_path, df)
    assert r.returncode == 0, r.stderr
    md = (out / "report.md").read_text()
    assert "pass --positive" in md
    assert "Flip rate" in md


def test_bad_inputs_exit_2_with_a_message(tmp_path, full):
    r = run("analyze", table(tmp_path, full), "--verdict", "nope", "--out", str(tmp_path / "o"))
    assert r.returncode == 2 and "nope" in r.stderr
    r, _ = analyze(tmp_path, full, "--positive", "pass", "--compare", "A", "Z")
    assert r.returncode == 2 and "Z" in r.stderr
    r, _ = analyze(tmp_path, full, "--positive", "yes")
    assert r.returncode == 2 and "yes" in r.stderr


def test_weight_and_by_columns(tmp_path, full):
    df = full.copy()
    df["w"] = [1.0 if int(i[1:]) % 2 else 3.0 for i in df["item"]]
    df["kind"] = ["table" if int(i[1:]) % 3 else "text" for i in df["item"]]
    r, out = analyze(tmp_path, df, "--positive", "pass", "--weight", "w", "--by", "kind")
    assert r.returncode == 0, r.stderr
    md = (out / "report.md").read_text()
    assert "Bias by kind" in md and "sampling weights" in md


def test_simulate_roundtrip(tmp_path):
    p = tmp_path / "sim.csv"
    r = run(
        "simulate",
        "--out",
        str(p),
        "--items",
        "40",
        "--trials",
        "2",
        "--judge",
        "strict:0.05:A=0.3/B=0.05:0.1",
        "--judge",
        "fair",
    )
    assert r.returncode == 0, r.stderr
    df = pd.read_csv(p)
    assert len(df) == 40 * 2 * 2 * 2
    r = run(
        "analyze",
        str(p),
        "--system",
        "system",
        "--reference",
        "reference",
        "--positive",
        "pass",
        "--out",
        str(tmp_path / "o"),
        "--n-boot",
        "50",
    )
    assert r.returncode == 0, r.stderr
