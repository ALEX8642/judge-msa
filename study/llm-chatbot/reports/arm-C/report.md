# Judge measurement system analysis

870 verdicts on 58 answers (29 questions) from 3 judge(s): gemma3:27b, mistral-small3.2:24b, phi4:14b. 58 answers have a reference verdict. Pass = “pass”.

## What difference can each judge resolve?

**gemma3:27b reports v2 − v1 = +24.1 points.** On 29 questions with 5 trial(s) it can resolve differences above **20.4 points**: 3.2 points from judge noise, which more trials or questions shrink, plus up to 17.2 points from bias between the two systems, which they do not. The reported difference is larger than that.

**mistral-small3.2:24b reports v2 − v1 = +24.8 points.** On 29 questions with 5 trial(s) it can resolve differences above **27.0 points**: 2.9 points from judge noise, which more trials or questions shrink, plus up to 24.1 points from bias between the two systems, which they do not. The reported difference is not larger than that.

**phi4:14b reports v2 − v1 = +59.3 points.** On 29 questions with 5 trial(s) it can resolve differences above **47.4 points**: 3.0 points from judge noise, which more trials or questions shrink, plus up to 44.4 points from bias between the two systems, which they do not. The reported difference is larger than that.

The judges' own figures for v2 − v1 differ from each other by 35.2 points.

## Repeatability: does a judge agree with itself?

The same judge grading the same answer again. Flip rate is the chance that two trials of one answer disagree.

| Judge | Answers | Trials | All trials agree | Flip rate | Kappa |
|---|---|---|---|---|---|
| gemma3:27b | 58 | 5 | 0.931 | 0.038 | 0.907 |
| mistral-small3.2:24b | 58 | 5 | 0.931 | 0.031 | 0.935 |
| phi4:14b | 58 | 5 | 0.931 | 0.034 | 0.931 |

## Reproducibility: do judges agree with each other?

On 58 answers graded by every judge, all judges agreed on every trial for 62.1%. Fleiss' kappa across judges: 0.548.

| Judge | Judge | Agreement | Cohen's kappa |
|---|---|---|---|
| gemma3:27b | mistral-small3.2:24b | 0.879 | 0.734 |
| gemma3:27b | phi4:14b | 0.690 | 0.407 |
| mistral-small3.2:24b | phi4:14b | 0.776 | 0.561 |

## Against the reference

A miss is a pass given to an answer the reference fails; a false alarm is a fail given to an answer the reference passes.

| Judge | System | Answers | Agreement | Kappa | Miss rate | False-alarm rate |
|---|---|---|---|---|---|---|
| gemma3:27b | v1 | 29 | 0.869 | 0.737 | 0.081 | 0.170 |
| gemma3:27b | v2 | 29 | 0.949 | 0.792 | 0.000 | 0.058 |
| mistral-small3.2:24b | v1 | 29 | 0.813 | 0.634 | 0.027 | 0.312 |
| mistral-small3.2:24b | v2 | 29 | 0.876 | 0.591 | 0.000 | 0.141 |
| phi4:14b | v1 | 29 | 0.675 | 0.390 | 0.000 | 0.577 |
| phi4:14b | v2 | 29 | 0.897 | 0.641 | 0.000 | 0.117 |

## Bias: judge score minus reference score

In points, on the answers that have a reference, with 95% intervals. A judge that is equally biased on every system still ranks them fairly; a difference in bias between systems does not wash out.

| Judge | System | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | v1 | 29 | 0.503 | 0.564 | -6.1 | -21.2 | +4.7 |
| gemma3:27b | v2 | 29 | 0.831 | 0.882 | -5.1 | -11.0 | -0.5 |
| mistral-small3.2:24b | v1 | 29 | 0.399 | 0.564 | -16.4 | -34.1 | -2.3 |
| mistral-small3.2:24b | v2 | 29 | 0.758 | 0.882 | -12.4 | -26.3 | -3.5 |
| phi4:14b | v1 | 29 | 0.238 | 0.564 | -32.5 | -51.2 | -17.4 |
| phi4:14b | v2 | 29 | 0.779 | 0.882 | -10.3 | -24.2 | -2.1 |

### Bias by category

| Judge | Category | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | figure | 2 | 1.000 | 1.000 | +0.0 | too few | too few |
| gemma3:27b | multi_page | 2 | 0.000 | 1.000 | -100.0 | too few | too few |
| gemma3:27b | single_page | 36 | 0.680 | 0.689 | -0.8 | -6.2 | +4.5 |
| gemma3:27b | table | 18 | 0.648 | 0.780 | -13.2 | -36.8 | +0.0 |
| mistral-small3.2:24b | figure | 2 | 1.000 | 1.000 | +0.0 | too few | too few |
| mistral-small3.2:24b | multi_page | 2 | 0.200 | 1.000 | -80.0 | too few | too few |
| mistral-small3.2:24b | single_page | 36 | 0.614 | 0.689 | -7.5 | -18.2 | +0.0 |
| mistral-small3.2:24b | table | 18 | 0.496 | 0.780 | -28.4 | -54.6 | -4.6 |
| phi4:14b | figure | 2 | 0.600 | 1.000 | -40.0 | too few | too few |
| phi4:14b | multi_page | 2 | 0.500 | 1.000 | -50.0 | too few | too few |
| phi4:14b | single_page | 36 | 0.518 | 0.689 | -17.1 | -28.2 | -8.0 |
| phi4:14b | table | 18 | 0.484 | 0.780 | -29.5 | -53.0 | -9.1 |

### Bias by selected

| Judge | Selected | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | no | 28 | 0.643 | 0.679 | -3.6 | -12.1 | +2.9 |
| gemma3:27b | yes | 30 | 0.780 | 0.933 | -15.3 | -35.3 | +0.0 |
| mistral-small3.2:24b | no | 28 | 0.564 | 0.679 | -11.4 | -23.6 | +0.0 |
| mistral-small3.2:24b | yes | 30 | 0.647 | 0.933 | -28.7 | -50.7 | -8.7 |
| phi4:14b | no | 28 | 0.529 | 0.679 | -15.0 | -26.4 | -4.3 |
| phi4:14b | yes | 30 | 0.413 | 0.933 | -52.0 | -66.0 | -38.0 |

### Difference in bias, v2 minus v1

| Judge | Reference questions | Difference in bias (pts) | Low | High |
|---|---|---|---|---|
| gemma3:27b | 29 | +0.9 | -11.3 | +17.2 |
| mistral-small3.2:24b | 29 | +4.0 | -15.3 | +24.1 |
| phi4:14b | 29 | +22.2 | +0.3 | +44.4 |

### v2 minus v1, as each judge scores it (all answers)

| Judge | v2 | v1 | Difference (pts) | Low | High |
|---|---|---|---|---|---|
| gemma3:27b | 0.834 | 0.593 | +24.1 | +4.8 | +44.1 |
| mistral-small3.2:24b | 0.731 | 0.483 | +24.8 | +2.8 | +46.2 |
| phi4:14b | 0.766 | 0.172 | +59.3 | +35.2 | +79.3 |

## Where the variation comes from

Share of the variance in pass/fail verdicts due to the answers themselves (part), to judges being stricter or more lenient overall (judge), to judges disagreeing about particular answers (judge × part), and to a judge disagreeing with itself (repeatability). The measurement system accounts for 41.6% of the variance.

| Component | Variance | Share |
|---|---|---|
| part | 0.145 | 0.584 |
| judge | 0.015 | 0.061 |
| judge_x_part | 0.071 | 0.286 |
| repeatability | 0.017 | 0.069 |

## What this data cannot tell you

- Reference statistics use the sampling weights in the weight column.
- Bias is measured against the reference as given. Errors in the reference shift every judge's bias, and the reference's own repeatability is not measured here unless it was entered as a judge with repeated trials.
- Bias bound comes from 29 reference items; a larger reference set tightens it, more trials do not.
