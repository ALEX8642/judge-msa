"""Print the numbers behind docs/validation.md. Run: uv run python scripts/validation_table.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

import test_validation as tv  # noqa: E402

from judge_msa.simulate import JudgeSpec  # noqa: E402

print(f"planted differential bias: {tv.planted_diff_bias():.4f}")
print(f"coverage of 95% interval (200 sims, 300 items): {tv.coverage():.3f}")
print(f"MRD exceedance, planted bias (300 sims): {tv.exceedance():.3f}")
print(f"MRD exceedance, no bias (300 sims): {tv.exceedance(spec=JudgeSpec(flip=0.05)):.3f}")
for n in (200, 2000):
    print(f"median bias bound, no bias, {n} items: {tv.bias_bound_median(n):.4f}")
