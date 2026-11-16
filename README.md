# judge-msa

[![CI](https://github.com/ALEX8642/judge-msa/actions/workflows/ci.yml/badge.svg)](https://github.com/ALEX8642/judge-msa/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A gauge study for LLM judges.** When an eval says system A beat system B by 8 points according to an LLM judge,
how small a difference can that judge actually be trusted on? Manufacturing answers this for every measuring
instrument before using it, with a measurement system analysis (MSA, or Gage R&R). judge-msa runs one on a table of
judge verdicts and reports, in points, the smallest difference the judge can resolve.

It never calls a model. You bring the verdicts.

## A worked result

Applied to the judges of [LLM-chatbot](https://github.com/ALEX8642/LLM-chatbot), a document-QA project whose v2 was
reported 38 points ahead of v1 ([full study](study/llm-chatbot/README.md), protocol committed before the runs):

- At temperature 0 the judges repeated themselves on 99.7 to 100% of answers. Reordering the key facts in the prompt
  still changed the verdict on about 7% of answers, for all three judges.
- Each judge could resolve a v2 − v1 difference only above **19 to 21 points**, almost all of it from uncertainty about
  bias between the two systems, which more judge runs cannot reduce. The reported lead cleared that; a 10-point lead
  would not have.
- The judge's known bias against v1 was 44 points on answers picked for being disputed and 2 points on answers drawn
  at random.
- The judge server's context window, a default nobody had set or recorded, changed verdicts on long inputs.

"The judge ran at temperature 0" is not an answer to any of this:
[why not](docs/why-not-just-temperature-zero.md).

## Five-minute start

```
uv tool install git+https://github.com/ALEX8642/judge-msa    # or: pip install git+https://...

# a simulated table to try it on: two systems, one judge that is lenient on system A
judge-msa simulate --out verdicts.csv --items 1000 --trials 3 --seed 2 \
    --systems A=0.7,B=0.7 --judge lenient:0.05:A=0.25/B=0.05:0

judge-msa analyze verdicts.csv --system system --reference reference \
    --positive pass --compare A B --out report
```

This writes `report/report.html` (self-contained), `report.md` and `result.json`. The two systems are equally good
by construction. The judge reports A ahead by 4.8 points, and the report says it cannot resolve differences below
8.5 points, nearly all of that from its bias towards A.

## Input

One row per verdict, as CSV, JSONL or Parquet. Column names are yours; map them with flags.

| Column | Flag | Needed | Meaning |
|---|---|---|---|
| item | `--item` | yes | the question |
| judge | `--judge` | yes | which judge (model, prompt or setup) gave the verdict |
| verdict | `--verdict` | yes | a category, e.g. pass / fail; name the passing one with `--positive` |
| trial | `--trial` | for repeatability | 0, 1, 2 … for repeated gradings of the same answer |
| system | `--system` | to compare systems | which system wrote the answer |
| reference | `--reference` | for bias | a trusted verdict (usually human) for some or all answers |
| weight | `--weight` | if the reference sample was not random | sampling weight of each reference answer |

Rows with an empty verdict (judge errors) are dropped and counted.

## What is reported

- **Repeatability:** does a judge give the same verdict again? Share of answers where all trials agree, flip rate,
  Fleiss' kappa.
- **Reproducibility:** do judges agree with each other? Pairwise Cohen's kappa, Fleiss' kappa.
- **Against the reference:** agreement, kappa, miss rate (passes a bad answer) and false-alarm rate (fails a good one).
- **Bias:** judge score minus reference score, per system or any column (`--by`), and its difference between two
  systems, with 95% bootstrap intervals that resample questions.
- **Variance components:** how much of the variation in verdicts comes from the answers, from judges, and from a
  judge disagreeing with itself.
- **Minimum resolvable difference (MRD):** for `--compare A B`, per judge: `noise + bias bound`. Noise is the 95%
  half-width from trial-to-trial variation at your number of questions and trials. The bias bound is the larger end
  of the 95% interval for the difference in bias between A and B. An observed difference below the MRD could be
  produced by the judge alone.
- **What this data cannot tell you:** every statistic the table could not support, and why. One trial per answer
  means no repeatability; no reference means no bias, and the report says that judges which agree may share a bias.

## How to design the study

Advice the worked study paid for:

- **Repeat in a way that should not matter.** At temperature 0, sending the same request again tests almost nothing.
  Reorder the rubric, reformat the answer, change the seed, move to another machine. Each is a `trial`.
- **Draw the reference sample at random**, or record how it was drawn and pass `--weight`. A reference set made of
  disputed cases measures the judge at its worst and says little about the eval as a whole.
- **Use more than one judge**, but do not read their agreement as correctness.
- **Write down the judge's full setup**: model digest, runtime version, context window, output limit. Treat a changed
  default as a different gauge.
- **Spend on the reference.** In the worked study, judge noise was under half a point and the bias bound was 20.
  Thirty more human-graded answers would have helped more than thirty thousand more judge calls.

## Is the arithmetic right?

Every estimator is tested on simulated tables with planted judge behaviour: [docs/validation.md](docs/validation.md).
In short: the bias interval covers the planted value 95.5% of the time, and the MRD is conservative (exceeded in 0.3%
of simulations against a nominal 5%), so it can call a real difference unresolved but should not call an artefact
resolved.

## Limits

- Categorical verdicts only; bias, variance components and MRD need a binary pass/fail.
- The MRD is a conservative bound, not a power calculation.
- Bias is relative to your reference. If the reference is wrong, so is the bias. Enter the human grader as a judge
  with repeated trials to measure the reference's own repeatability.
- The simulation model behind the validation is simple; real judges err in ways that depend on the question.

## Development

```
uv sync
uv run pytest            # fast tests
uv run pytest -m slow    # statistical validation, about a minute
uv run ruff check . && uv run ruff format --check .
```

MIT licence. Built with AI coding agents; design, protocol and review by Alexander Feht.
