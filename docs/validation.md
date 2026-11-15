# Validation against planted truth

Every estimator is tested on simulated verdict tables where the right answer is known because it was planted
(`src/judge_msa/simulate.py`). The fast tests (`pytest -m "not slow"`) check point recovery; the slow ones
(`pytest -m slow`, `tests/test_validation.py`) check the statistical claims below. Regenerate the numbers with
`uv run python scripts/validation_table.py`.

## The simulation model

Each part (question × system) has a true outcome. A judge holds a persistent opinion of each part, wrong with a
planted miss rate (passes a bad answer) or false-alarm rate (fails a good one), which may differ by system. Each trial
reports that opinion, flipped with a planted probability.

## Results (seeded; 2026-11-15)

| Claim | Setup | Result |
|---|---|---|
| The 95% interval for differential bias covers the planted value about 95% of the time | 200 simulations; 300 questions, 2 systems, 3 trials; miss rate 0.25 on system A and 0.05 on B (planted differential bias 0.054) | covered in **95.5%** |
| A judged difference is rarely further from the true difference than the MRD | 300 simulations; 170 questions, reference on 50 of them, same planted bias, equal true quality | exceeded in **0.3%** (nominal ceiling 5%) |
| Same, with an unbiased judge | as above, no planted bias, flip rate 0.05 | exceeded in **0.0%** |
| With no bias, the bias bound shrinks as the reference set grows | median bias bound at 200 vs 2,000 reference questions | **0.035 → 0.011** |

Also checked in the fast tests: flip rates, miss and false-alarm rates, repeatability variance, judge and
judge-by-part variance components and per-system bias are each recovered within a stated tolerance; Cohen's kappa
matches a textbook table; Fleiss' kappa matches statsmodels when every part has the same number of ratings.

## What this shows and does not show

- The MRD is **conservative**: it is exceeded far less often than 5%. It adds the worst end of the bias interval to
  the noise half-width instead of combining them, and the bias interval already contains some trial noise. It can
  therefore say "cannot resolve" for a difference a sharper method would resolve. It should not say "resolved" for one
  it cannot.
- The simulation model is simple. Real judges have errors that depend on the question, not only on the system, and a
  real reference has errors of its own. Validation on planted truth shows the arithmetic is right; it does not show
  the model fits a given judge.
- The bias bound is only as good as the reference. A reference with its own bias moves every judge's measured bias
  by the same amount.
