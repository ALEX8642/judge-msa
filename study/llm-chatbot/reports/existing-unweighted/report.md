# Judge measurement system analysis

675 verdicts on 338 answers (169 questions) from 2 judge(s): mistral-small3.2:24b, phi4:14b. 100 answers have a reference verdict. Pass = “pass”.

## What difference can each judge resolve?

**mistral-small3.2:24b reports v2 − v1 = +33.7 points.** Its minimum resolvable difference is not estimable (only one trial per part: judge noise unknown); bias between the systems may be up to 16.0 points.

**phi4:14b reports v2 − v1 = +37.0 points.** Its minimum resolvable difference is not estimable (only one trial per part: judge noise unknown); bias between the systems may be up to 38.0 points.

The judges' own figures for v2 − v1 differ from each other by 3.3 points.

## Repeatability: does a judge agree with itself?

The same judge grading the same answer again. Flip rate is the chance that two trials of one answer disagree.

| Judge | Answers | Trials | All trials agree | Flip rate | Kappa |
|---|---|---|---|---|---|
| mistral-small3.2:24b | 338 | 1 | not estimable (only one trial per part) | not estimable (only one trial per part) | not estimable (only one trial per part) |
| phi4:14b | 337 | 1 | not estimable (only one trial per part) | not estimable (only one trial per part) | not estimable (only one trial per part) |

## Reproducibility: do judges agree with each other?

On 337 answers graded by every judge, all judges agreed on every trial for 91.4%. Fleiss' kappa across judges: 0.816.

| Judge | Judge | Agreement | Cohen's kappa |
|---|---|---|---|
| mistral-small3.2:24b | phi4:14b | 0.914 | 0.816 |

## Against the reference

A miss is a pass given to an answer the reference fails; a false alarm is a fail given to an answer the reference passes.

| Judge | System | Answers | Agreement | Kappa | Miss rate | False-alarm rate |
|---|---|---|---|---|---|---|
| mistral-small3.2:24b | v1 | 50 | 0.720 | 0.440 | 0.211 | 0.323 |
| mistral-small3.2:24b | v2 | 50 | 0.880 | 0.658 | 0.000 | 0.143 |
| phi4:14b | v1 | 50 | 0.560 | 0.197 | 0.158 | 0.613 |
| phi4:14b | v2 | 50 | 0.840 | 0.543 | 0.125 | 0.167 |

## Bias: judge score minus reference score

In points, on the answers that have a reference, with 95% intervals. A judge that is equally biased on every system still ranks them fairly; a difference in bias between systems does not wash out.

| Judge | System | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| mistral-small3.2:24b | v1 | 50 | 0.500 | 0.620 | -12.0 | -26.0 | +2.0 |
| mistral-small3.2:24b | v2 | 50 | 0.720 | 0.840 | -12.0 | -22.0 | -4.0 |
| phi4:14b | v1 | 50 | 0.300 | 0.620 | -32.0 | -48.0 | -16.0 |
| phi4:14b | v2 | 50 | 0.720 | 0.840 | -12.0 | -22.0 | -2.0 |

### Bias by selected

| Judge | Selected | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| mistral-small3.2:24b | no | 58 | 0.552 | 0.603 | -5.2 | -15.5 | +5.2 |
| mistral-small3.2:24b | yes | 42 | 0.690 | 0.905 | -21.4 | -39.5 | -4.8 |
| phi4:14b | no | 58 | 0.603 | 0.603 | +0.0 | -8.6 | +8.6 |
| phi4:14b | yes | 42 | 0.381 | 0.905 | -52.4 | -65.8 | -37.5 |

### Difference in bias, v2 minus v1

| Judge | Reference questions | Difference in bias (pts) | Low | High |
|---|---|---|---|---|
| mistral-small3.2:24b | 50 | +0.0 | -16.0 | +14.0 |
| phi4:14b | 50 | +20.0 | +2.0 | +38.0 |

### v2 minus v1, as each judge scores it (all answers)

| Judge | v2 | v1 | Difference (pts) | Low | High |
|---|---|---|---|---|---|
| mistral-small3.2:24b | 0.805 | 0.467 | +33.7 | +25.4 | +42.0 |
| phi4:14b | 0.805 | 0.435 | +37.0 | +29.0 | +45.7 |

## Where the variation comes from

Share of the variance in pass/fail verdicts due to the answers themselves (part), to judges being stricter or more lenient overall (judge), to judges disagreeing about particular answers (judge × part), and to a judge disagreeing with itself (repeatability). The measurement system accounts for 18.4% of the variance.

| Component | Variance | Share |
|---|---|---|
| part | 0.191 | 0.816 |
| judge | 0.000 | 0.000 |
| judge_x_part | 0.043 | 0.183 |
| repeatability | not estimable (only one trial per part) | not estimable (only one trial per part) |

## What this data cannot tell you

- 1 row had no verdict and was left out.
- Bias is measured against the reference as given. Errors in the reference shift every judge's bias, and the reference's own repeatability is not measured here unless it was entered as a judge with repeated trials.
- Judge noise unknown: grade each answer more than once to measure it.
- Bias bound comes from 50 reference items; a larger reference set tightens it, more trials do not.
