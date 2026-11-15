# Judge measurement system analysis

675 verdicts on 338 answers (169 questions) from 2 judge(s): mistral-small3.2:24b, phi4:14b. 100 answers have a reference verdict. Pass = “pass”.

## What difference can each judge resolve?

**mistral-small3.2:24b reports v2 − v1 = +33.7 points.** Its minimum resolvable difference is not estimable (only one trial per part: judge noise unknown); bias between the systems may be up to 20.0 points.

**phi4:14b reports v2 − v1 = +37.0 points.** Its minimum resolvable difference is not estimable (only one trial per part: judge noise unknown); bias between the systems may be up to 15.5 points.

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
| mistral-small3.2:24b | v1 | 50 | 0.723 | 0.440 | 0.184 | 0.380 |
| mistral-small3.2:24b | v2 | 50 | 0.940 | 0.828 | 0.000 | 0.074 |
| phi4:14b | v1 | 50 | 0.748 | 0.492 | 0.172 | 0.339 |
| phi4:14b | v2 | 50 | 0.928 | 0.794 | 0.031 | 0.081 |

## Bias: judge score minus reference score

In points, on the answers that have a reference, with 95% intervals. A judge that is equally biased on every system still ranks them fairly; a difference in bias between systems does not wash out.

| Judge | System | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| mistral-small3.2:24b | v1 | 50 | 0.391 | 0.475 | -8.4 | -25.9 | +8.6 |
| mistral-small3.2:24b | v2 | 50 | 0.747 | 0.807 | -6.0 | -13.5 | -1.2 |
| phi4:14b | v1 | 50 | 0.404 | 0.475 | -7.0 | -21.4 | +7.5 |
| phi4:14b | v2 | 50 | 0.747 | 0.807 | -6.0 | -13.6 | -1.1 |

### Bias by category

| Judge | Category | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| mistral-small3.2:24b | figure | 2 | 1.000 | 1.000 | +0.0 | too few | too few |
| mistral-small3.2:24b | multi_page | 2 | 0.000 | 1.000 | -100.0 | too few | too few |
| mistral-small3.2:24b | single_page | 46 | 0.619 | 0.675 | -5.6 | -14.6 | +0.5 |
| mistral-small3.2:24b | table | 32 | 0.461 | 0.644 | -18.2 | -33.8 | -5.3 |
| mistral-small3.2:24b | unanswerable | 18 | 0.622 | 0.561 | +6.1 | -21.8 | +33.3 |
| phi4:14b | figure | 2 | 0.500 | 1.000 | -50.0 | too few | too few |
| phi4:14b | multi_page | 2 | 0.500 | 1.000 | -50.0 | too few | too few |
| phi4:14b | single_page | 46 | 0.557 | 0.675 | -11.8 | -23.1 | -4.7 |
| phi4:14b | table | 32 | 0.462 | 0.644 | -18.1 | -34.0 | -6.7 |
| phi4:14b | unanswerable | 18 | 0.756 | 0.561 | +19.5 | +1.6 | +37.8 |

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
| mistral-small3.2:24b | 50 | +2.4 | -15.7 | +20.0 |
| phi4:14b | 50 | +1.1 | -14.6 | +15.5 |

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
- Reference statistics use the sampling weights in the weight column.
- Bias is measured against the reference as given. Errors in the reference shift every judge's bias, and the reference's own repeatability is not measured here unless it was entered as a judge with repeated trials.
- Judge noise unknown: grade each answer more than once to measure it.
- Bias bound comes from 50 reference items; a larger reference set tightens it, more trials do not.
