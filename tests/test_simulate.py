import pytest

from judge_msa.simulate import JudgeSpec, expected, simulate

SPEC = JudgeSpec(flip=0.1, miss={"A": 0.3, "B": 0.05}, false_alarm=0.1)


def test_shape_and_columns():
    df = simulate(50, {"A": 0.7, "B": 0.6}, {"j1": SPEC, "j2": JudgeSpec()}, 3, seed=1)
    assert len(df) == 50 * 2 * 2 * 3
    assert set(df["verdict"]) <= {"pass", "fail"}
    assert df["reference"].notna().all()


def test_seed_is_deterministic():
    a = simulate(30, {"A": 0.7}, {"j": SPEC}, 2, seed=5)
    b = simulate(30, {"A": 0.7}, {"j": SPEC}, 2, seed=5)
    c = simulate(30, {"A": 0.7}, {"j": SPEC}, 2, seed=6)
    assert a.equals(b)
    assert not a.equals(c)


@pytest.mark.parametrize("system", ["A", "B"])
def test_empirical_score_matches_expected(system):
    df = simulate(20000, {"A": 0.7, "B": 0.7}, {"j": SPEC}, 2, seed=2)
    d = df[df["system"] == system]
    score = (d["verdict"] == "pass").mean()
    exp = expected(SPEC, system, 0.7)
    assert score == pytest.approx(exp["score"], abs=0.01)
    assert exp["bias"] == pytest.approx(exp["score"] - 0.7)
    assert exp["rep_var"] == pytest.approx(0.09)


def test_expected_values_by_hand():
    # p=0.7, fa=0.1, miss=0.3: q = 0.7*0.9 + 0.3*0.3 = 0.72; score = 0.72*0.9 + 0.28*0.1 = 0.676
    assert expected(SPEC, "A", 0.7)["score"] == pytest.approx(0.676)


def test_zero_flip_trials_identical():
    df = simulate(200, {"A": 0.5}, {"j": JudgeSpec(flip=0.0, miss=0.2)}, 4, seed=3)
    assert (df.groupby(["item", "system", "judge"])["verdict"].nunique() == 1).all()


def test_ref_fraction_blanks_whole_items():
    df = simulate(400, {"A": 0.5, "B": 0.5}, {"j": JudgeSpec()}, 1, ref_fraction=0.25, seed=4)
    per_item = df.groupby("item")["reference"].apply(lambda s: s.notna().mean())
    assert set(per_item.unique()) <= {0.0, 1.0}
    assert per_item.mean() == pytest.approx(0.25, abs=0.01)
