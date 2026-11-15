import pandas as pd
import pytest

from judge_msa.table import NotEstimable, TableError, load_table, validate


def _rows(n=4):
    return pd.DataFrame(
        {
            "q": [f"q{i}" for i in range(n)],
            "model": ["phi"] * n,
            "rep": [0] * n,
            "grade": ["pass", "fail"] * (n // 2),
        }
    )


def test_column_mapping_csv(tmp_path):
    p = tmp_path / "t.csv"
    _rows().to_csv(p, index=False)
    df = load_table(p, item="q", judge="model", trial="rep", verdict="grade")
    assert list(df.columns[:6]) == ["item", "system", "judge", "trial", "verdict", "reference"]
    assert set(df["system"]) == {"_"}
    assert df["reference"].isna().all()
    assert len(df) == 4


def test_jsonl_and_parquet(tmp_path):
    r = _rows()
    r.to_json(tmp_path / "t.jsonl", orient="records", lines=True)
    r.to_parquet(tmp_path / "t.parquet")
    for name in ("t.jsonl", "t.parquet"):
        df = load_table(tmp_path / name, item="q", judge="model", trial="rep", verdict="grade")
        assert len(df) == 4


def test_missing_trial_column_becomes_zero(tmp_path):
    p = tmp_path / "t.csv"
    _rows().drop(columns="rep").to_csv(p, index=False)
    df = load_table(p, item="q", judge="model", verdict="grade")
    assert (df["trial"] == 0).all()


def test_by_columns_kept(tmp_path):
    p = tmp_path / "t.csv"
    _rows().assign(category="table").to_csv(p, index=False)
    df = load_table(p, item="q", judge="model", trial="rep", verdict="grade", by=("category",))
    assert "category" in df.columns


def test_na_verdicts_dropped_and_counted():
    df = pd.DataFrame(
        {
            "item": [f"q{i}" for i in range(10)],
            "judge": "j",
            "trial": 0,
            "verdict": ["pass"] * 7 + [None] * 3,
        }
    )
    out = validate(df)
    assert len(out) == 7
    assert out.attrs["dropped"] == 3


def test_duplicate_key_raises_with_key():
    df = pd.DataFrame(
        {"item": ["q1", "q1"], "judge": ["j", "j"], "trial": [0, 0], "verdict": ["pass", "fail"]}
    )
    with pytest.raises(TableError, match="q1"):
        validate(df)


def test_inconsistent_reference_raises():
    df = pd.DataFrame(
        {
            "item": ["q1", "q1"],
            "system": ["A", "A"],
            "judge": ["j", "k"],
            "trial": [0, 0],
            "verdict": ["pass", "fail"],
            "reference": ["pass", "fail"],
        }
    )
    with pytest.raises(TableError, match="q1"):
        validate(df)


def test_missing_required_column_raises(tmp_path):
    p = tmp_path / "t.csv"
    _rows().to_csv(p, index=False)
    with pytest.raises(TableError, match="verdict"):
        load_table(p, item="q", judge="model", trial="rep")


def test_verdicts_are_strings_even_if_bool():
    df = pd.DataFrame({"item": ["a", "b"], "judge": "j", "trial": 0, "verdict": [True, False]})
    out = validate(df)
    assert set(out["verdict"]) == {"True", "False"}


def test_not_estimable_carries_reason():
    assert NotEstimable("one trial").reason == "one trial"
