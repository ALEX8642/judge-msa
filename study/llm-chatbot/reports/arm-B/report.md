# Judge measurement system analysis

5047 verdicts on 338 answers (169 questions) from 3 judge(s): gemma3:27b, mistral-small3.2:24b, phi4:14b. 100 answers have a reference verdict. Pass = “pass”.

## What difference can each judge resolve?

**gemma3:27b reports v2 − v1 = +29.9 points.** On 168 questions with 5 trial(s) it can resolve differences above **21.9 points**: 0.4 points from judge noise, which more trials or questions shrink, plus up to 21.5 points from bias between the two systems, which they do not. The reported difference is larger than that.

**mistral-small3.2:24b reports v2 − v1 = +31.7 points.** On 169 questions with 5 trial(s) it can resolve differences above **18.7 points**: 1.2 points from judge noise, which more trials or questions shrink, plus up to 17.5 points from bias between the two systems, which they do not. The reported difference is larger than that.

**phi4:14b reports v2 − v1 = +38.5 points.** On 168 questions with 5 trial(s) it can resolve differences above **23.9 points**: 1.7 points from judge noise, which more trials or questions shrink, plus up to 22.3 points from bias between the two systems, which they do not. The reported difference is larger than that.

The judges' own figures for v2 − v1 differ from each other by 8.7 points.

## Repeatability: does a judge agree with itself?

The same judge grading the same answer again. Flip rate is the chance that two trials of one answer disagree.

| Judge | Answers | Trials | All trials agree | Flip rate | Kappa |
|---|---|---|---|---|---|
| gemma3:27b | 336 | 5 | 0.994 | 0.003 | 0.993 |
| mistral-small3.2:24b | 338 | 5 | 0.941 | 0.031 | 0.933 |
| phi4:14b | 337 | 5 | 0.893 | 0.060 | 0.874 |

## Reproducibility: do judges agree with each other?

On 335 answers graded by every judge, all judges agreed on every trial for 81.5%. Fleiss' kappa across judges: 0.815.

| Judge | Judge | Agreement | Cohen's kappa |
|---|---|---|---|
| gemma3:27b | mistral-small3.2:24b | 0.955 | 0.901 |
| gemma3:27b | phi4:14b | 0.901 | 0.788 |
| mistral-small3.2:24b | phi4:14b | 0.887 | 0.760 |

## Against the reference

A miss is a pass given to an answer the reference fails; a false alarm is a fail given to an answer the reference passes.

| Judge | System | Answers | Agreement | Kappa | Miss rate | False-alarm rate |
|---|---|---|---|---|---|---|
| gemma3:27b | v1 | 50 | 0.817 | 0.634 | 0.195 | 0.170 |
| gemma3:27b | v2 | 50 | 0.946 | 0.840 | 0.031 | 0.059 |
| mistral-small3.2:24b | v1 | 50 | 0.733 | 0.460 | 0.184 | 0.360 |
| mistral-small3.2:24b | v2 | 50 | 0.923 | 0.786 | 0.000 | 0.095 |
| phi4:14b | v1 | 50 | 0.691 | 0.375 | 0.177 | 0.452 |
| phi4:14b | v2 | 50 | 0.885 | 0.673 | 0.125 | 0.113 |

## Bias: judge score minus reference score

In points, on the answers that have a reference, with 95% intervals. A judge that is equally biased on every system still ranks them fairly; a difference in bias between systems does not wash out.

| Judge | System | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | v1 | 50 | 0.497 | 0.475 | +2.2 | -11.0 | +15.7 |
| gemma3:27b | v2 | 50 | 0.765 | 0.807 | -4.2 | -11.4 | +0.6 |
| mistral-small3.2:24b | v1 | 50 | 0.400 | 0.475 | -7.4 | -23.9 | +9.2 |
| mistral-small3.2:24b | v2 | 50 | 0.730 | 0.807 | -7.7 | -15.7 | -2.1 |
| phi4:14b | v1 | 50 | 0.351 | 0.475 | -12.4 | -27.8 | +3.6 |
| phi4:14b | v2 | 50 | 0.740 | 0.807 | -6.7 | -15.1 | +0.3 |

### Bias by category

| Judge | Category | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | figure | 2 | 1.000 | 1.000 | +0.0 | too few | too few |
| gemma3:27b | multi_page | 2 | 0.000 | 1.000 | -100.0 | too few | too few |
| gemma3:27b | single_page | 46 | 0.640 | 0.675 | -3.5 | -12.1 | +2.1 |
| gemma3:27b | table | 32 | 0.525 | 0.644 | -11.9 | -25.2 | -0.4 |
| gemma3:27b | unanswerable | 18 | 0.756 | 0.561 | +19.5 | +1.9 | +38.1 |
| mistral-small3.2:24b | figure | 2 | 1.000 | 1.000 | +0.0 | too few | too few |
| mistral-small3.2:24b | multi_page | 2 | 0.000 | 1.000 | -100.0 | too few | too few |
| mistral-small3.2:24b | single_page | 46 | 0.619 | 0.675 | -5.6 | -14.1 | +0.0 |
| mistral-small3.2:24b | table | 32 | 0.440 | 0.644 | -20.4 | -38.6 | -4.7 |
| mistral-small3.2:24b | unanswerable | 18 | 0.634 | 0.561 | +7.3 | -18.8 | +33.3 |
| phi4:14b | figure | 2 | 0.700 | 1.000 | -30.0 | too few | too few |
| phi4:14b | multi_page | 2 | 0.600 | 1.000 | -40.0 | too few | too few |
| phi4:14b | single_page | 46 | 0.506 | 0.675 | -16.9 | -27.0 | -8.9 |
| phi4:14b | table | 32 | 0.400 | 0.644 | -24.4 | -39.5 | -10.9 |
| phi4:14b | unanswerable | 18 | 0.793 | 0.561 | +23.2 | +7.1 | +40.4 |

### Bias by selected

| Judge | Selected | Answers | Judge score | Reference score | Bias (pts) | Low | High |
|---|---|---|---|---|---|---|---|
| gemma3:27b | no | 58 | 0.607 | 0.603 | +0.3 | -8.3 | +9.0 |
| gemma3:27b | yes | 42 | 0.800 | 0.905 | -10.5 | -27.1 | +3.8 |
| mistral-small3.2:24b | no | 58 | 0.545 | 0.603 | -5.9 | -16.6 | +5.2 |
| mistral-small3.2:24b | yes | 42 | 0.710 | 0.905 | -19.5 | -35.2 | -5.2 |
| phi4:14b | no | 58 | 0.548 | 0.603 | -5.5 | -15.5 | +4.8 |
| phi4:14b | yes | 42 | 0.524 | 0.905 | -38.1 | -52.9 | -22.4 |

### Difference in bias, v2 minus v1

| Judge | Reference questions | Difference in bias (pts) | Low | High |
|---|---|---|---|---|
| gemma3:27b | 50 | -6.4 | -21.5 | +7.9 |
| mistral-small3.2:24b | 50 | -0.2 | -17.5 | +16.0 |
| phi4:14b | 50 | +5.7 | -11.4 | +22.3 |

### v2 minus v1, as each judge scores it (all answers)

| Judge | v2 | v1 | Difference (pts) | Low | High |
|---|---|---|---|---|---|
| gemma3:27b | 0.827 | 0.529 | +29.9 | +22.0 | +38.0 |
| mistral-small3.2:24b | 0.799 | 0.482 | +31.7 | +23.9 | +39.8 |
| phi4:14b | 0.795 | 0.410 | +38.5 | +31.1 | +46.6 |

## Where the variation comes from

Share of the variance in pass/fail verdicts due to the answers themselves (part), to judges being stricter or more lenient overall (judge), to judges disagreeing about particular answers (judge × part), and to a judge disagreeing with itself (repeatability). The measurement system accounts for 17.3% of the variance.

| Component | Variance | Share |
|---|---|---|
| part | 0.191 | 0.827 |
| judge | 0.001 | 0.006 |
| judge_x_part | 0.023 | 0.099 |
| repeatability | 0.016 | 0.068 |

## What this data cannot tell you

- Reference statistics use the sampling weights in the weight column.
- Bias is measured against the reference as given. Errors in the reference shift every judge's bias, and the reference's own repeatability is not measured here unless it was entered as a judge with repeated trials.
- Bias bound comes from 50 reference items; a larger reference set tightens it, more trials do not.
