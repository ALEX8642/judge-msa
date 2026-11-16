# Judge measurement system analysis

3030 verdicts on 338 answers (169 questions) from 3 judge(s): gemma3:27b, mistral-small3.2:24b, phi4:14b. 100 answers have a reference verdict. Pass = “pass”.

## What difference can each judge resolve?

**gemma3:27b reports v2 − v1 = +30.3 points.** On 167 questions with 3 trial(s) it can resolve differences above **21.1 points**: 0.0 points from judge noise, which more trials or questions shrink, plus up to 21.1 points from bias between the two systems, which they do not. The reported difference is larger than that.

**mistral-small3.2:24b reports v2 − v1 = +32.5 points.** On 169 questions with 3 trial(s) it can resolve differences above **19.4 points**: 0.0 points from judge noise, which more trials or questions shrink, plus up to 19.4 points from bias between the two systems, which they do not. The reported difference is larger than that.

**phi4:14b reports v2 − v1 = +37.4 points.** On 168 questions with 3 trial(s) it can resolve differences above **20.2 points**: 0.4 points from judge noise, which more trials or questions shrink, plus up to 19.8 points from bias between the two systems, which they do not. The reported difference is larger than that.

The judges' own figures for v2 − v1 differ from each other by 7.2 points.

## Repeatability: does a judge agree with itself?

The same judge grading the same answer again. Flip rate is the chance that two trials of one answer disagree.

| Judge | Answers | Trials | All trials agree | Flip rate | Kappa |
|---|---|---|---|---|---|
| gemma3:27b | 335 | 3 | 1.000 | 0.000 | 1.000 |
| mistral-small3.2:24b | 338 | 3 | 1.000 | 0.000 | 1.000 |
| phi4:14b | 337 | 3 | 0.997 | 0.002 | 0.996 |

## Reproducibility: do judges agree with each other?

On 334 answers graded by every judge, all judges agreed on every trial for 90.1%. Fleiss' kappa across judges: 0.856.

| Judge | Judge | Agreement | Cohen's kappa |
|---|---|---|---|
| gemma3:27b | mistral-small3.2:24b | 0.958 | 0.907 |
| gemma3:27b | phi4:14b | 0.928 | 0.843 |
| mistral-small3.2:24b | phi4:14b | 0.916 | 0.820 |

## Against the reference

A miss is a pass given to an answer the reference fails; a false alarm is a fail given to an answer the reference passes.

| Judge | System | Answers | Agreement | Kappa | Miss rate | False-alarm rate |
|---|---|---|---|---|---|---|
| gemma3:27b | v1 | 50 | 0.825 | 0.650 | 0.184 | 0.165 |
| gemma3:27b | v2 | 50 | 0.946 | 0.840 | 0.031 | 0.059 |
| mistral-small3.2:24b | v1 | 50 | 0.729 | 0.452 | 0.184 | 0.368 |
| mistral-small3.2:24b | v2 | 50 | 0.940 | 0.828 | 0.000 | 0.074 |
| phi4:14b | v1 | 50 | 0.726 | 0.446 | 0.172 | 0.386 |
| phi4:14b | v2 | 50 | 0.940 | 0.825 | 0.031 | 0.067 |

## Bias: judge score minus reference score

In points, on the answers that have a reference, with 95% intervals. A judge that is equally biased on every system still ranks them fairly; a difference in bias between systems does not wash out.

| Judge | System | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | v1 | 50 | 0.493 | 0.475 | +1.8 | -10.9 | +15.7 |
| gemma3:27b | v2 | 50 | 0.765 | 0.807 | -4.2 | -11.4 | +0.6 |
| mistral-small3.2:24b | v1 | 50 | 0.397 | 0.475 | -7.8 | -24.8 | +9.1 |
| mistral-small3.2:24b | v2 | 50 | 0.747 | 0.807 | -6.0 | -13.2 | -1.2 |
| phi4:14b | v1 | 50 | 0.382 | 0.475 | -9.3 | -24.2 | +5.6 |
| phi4:14b | v2 | 50 | 0.759 | 0.807 | -4.8 | -12.0 | +0.0 |

### Bias by category

| Judge | Category | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | figure | 2 | 1.000 | 1.000 | +0.0 | too few | too few |
| gemma3:27b | multi_page | 2 | 0.000 | 1.000 | -100.0 | too few | too few |
| gemma3:27b | single_page | 46 | 0.633 | 0.675 | -4.2 | -12.4 | +1.0 |
| gemma3:27b | table | 32 | 0.528 | 0.644 | -11.5 | -25.0 | +0.0 |
| gemma3:27b | unanswerable | 18 | 0.756 | 0.561 | +19.5 | +1.9 | +38.1 |
| mistral-small3.2:24b | figure | 2 | 1.000 | 1.000 | +0.0 | too few | too few |
| mistral-small3.2:24b | multi_page | 2 | 0.000 | 1.000 | -100.0 | too few | too few |
| mistral-small3.2:24b | single_page | 46 | 0.626 | 0.675 | -4.9 | -13.7 | +0.9 |
| mistral-small3.2:24b | table | 32 | 0.461 | 0.644 | -18.2 | -33.1 | -5.5 |
| mistral-small3.2:24b | unanswerable | 18 | 0.622 | 0.561 | +6.1 | -21.4 | +33.3 |
| phi4:14b | figure | 2 | 0.667 | 1.000 | -33.3 | too few | too few |
| phi4:14b | multi_page | 2 | 0.500 | 1.000 | -50.0 | too few | too few |
| phi4:14b | single_page | 46 | 0.557 | 0.675 | -11.8 | -21.8 | -5.5 |
| phi4:14b | table | 32 | 0.442 | 0.644 | -20.1 | -35.3 | -7.1 |
| phi4:14b | unanswerable | 18 | 0.756 | 0.561 | +19.5 | +1.9 | +38.1 |

### Bias by selected

| Judge | Selected | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | no | 58 | 0.603 | 0.603 | +0.0 | -8.6 | +8.6 |
| gemma3:27b | yes | 42 | 0.810 | 0.905 | -9.5 | -26.2 | +4.8 |
| mistral-small3.2:24b | no | 58 | 0.552 | 0.603 | -5.2 | -15.5 | +5.2 |
| mistral-small3.2:24b | yes | 42 | 0.714 | 0.905 | -19.0 | -35.7 | -4.8 |
| phi4:14b | no | 58 | 0.586 | 0.603 | -1.7 | -10.3 | +6.9 |
| phi4:14b | yes | 42 | 0.460 | 0.905 | -44.4 | -58.7 | -29.4 |

### Difference in bias, v2 minus v1

| Judge | Reference questions | Difference in bias (pts) | Low | High |
|---|---|---|---|---|
| gemma3:27b | 50 | -6.0 | -21.1 | +7.9 |
| mistral-small3.2:24b | 50 | +1.8 | -16.3 | +19.4 |
| phi4:14b | 50 | +4.5 | -11.9 | +19.8 |

### v2 minus v1, as each judge scores it (all answers)

| Judge | v2 | v1 | Difference (pts) | Low | High |
|---|---|---|---|---|---|
| gemma3:27b | 0.832 | 0.530 | +30.3 | +22.5 | +38.4 |
| mistral-small3.2:24b | 0.805 | 0.479 | +32.5 | +24.3 | +41.4 |
| phi4:14b | 0.805 | 0.431 | +37.4 | +29.3 | +45.8 |

## Where the variation comes from

Share of the variance in pass/fail verdicts due to the answers themselves (part), to judges being stricter or more lenient overall (judge), to judges disagreeing about particular answers (judge × part), and to a judge disagreeing with itself (repeatability). The measurement system accounts for 14.2% of the variance.

| Component | Variance | Share |
|---|---|---|
| part | 0.196 | 0.858 |
| judge | 0.001 | 0.004 |
| judge_x_part | 0.031 | 0.137 |
| repeatability | 0.000 | 0.001 |

## What this data cannot tell you

- Reference statistics use the sampling weights in the weight column.
- Bias is measured against the reference as given. Errors in the reference shift every judge's bias, and the reference's own repeatability is not measured here unless it was entered as a judge with repeated trials.
- Bias bound comes from 50 reference items; a larger reference set tightens it, more trials do not.
