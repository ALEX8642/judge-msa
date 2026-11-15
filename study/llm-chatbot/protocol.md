# Study protocol: measurement system analysis of LLM-chatbot's judges

Written and committed **before** any new judging run. Deviations are logged at the end, with the date and the reason.

## Question

LLM-chatbot reported that its v2 pipeline beat v1 by about 38 points on a registered test, graded by a local LLM judge.
Blind human grading later showed the judge treated the two systems' citation styles differently. This study asks, as
a gauge study would: how repeatable is each judge, how well do judges agree, how biased is each against the human
reference, and what is the smallest v2-v1 difference each judge can resolve?

It is not a re-test of v2 against v1 and it changes no published LLM-chatbot result.

## Inputs (all public, from LLM-chatbot at commit `9354dee55718de7967813c17bfa1ec7b0f707c21`)

- **Parts:** the first-repeat answers of v1 and v2 to the 169 frozen test questions: 338 answers
  (`evals/results/raw/{v1,v2}-test.json`, `evals/test.jsonl`). These are the answers the blind session showed.
- **Reference:** the blind human grades of 100 of those answers (50 questions x 2 systems,
  `evals/sessions/blind_grades.jsonl`, key `blind_key.json`). One grader, not a subject expert.
  A human **pass** is, as in LLM-chatbot's TEST.md: graded "correct" with the cited pages showing it, or a decline on
  an unanswerable question. "Partly", "wrong", unsupported, and declines on answerable questions are fails.
- **The reference sample was not random.** 21 questions were chosen because a judge had rejected or disputed them;
  29 were drawn at random from the remaining 148. Reference-based statistics therefore use sampling weights:
  1 for the 21 chosen questions, 148/29 for the 29 random ones. Unweighted figures are shown beside them, labelled
  as describing the enriched sample only.
- **Existing grades:** phi4:14b and mistral-small3.2:24b, one grading per answer, run on a 16 GB laptop GPU through
  Ollama (`evals/results/test/*.json`).

## Judges (appraisers)

`phi4:14b`, `mistral-small3.2:24b` (the registered judges) and `gemma3:27b` (added so that agreement between
judges rests on more than one pair; a family no compared system uses). All use LLM-chatbot's own grader and judge
prompt version 2, unchanged, driven by `rejudge.py`.

Setup for the new runs: Ollama 0.40.16 on an RTX 5090 (32 GB), one model loaded at a time, context window 16,384
tokens (set explicitly with `OLLAMA_CONTEXT_LENGTH`), max 1,500 output tokens. Model digests: phi4 `ac896e5b8b34`,
mistral-small3.2 `5a408ab55df5`, gemma3 `6be2e2ba6843`.

## Arms

| Arm | What changes between trials | Settings | Parts | Trials per judge |
|---|---|---|---|---|
| **A** registered settings | nothing but the seed | temperature 0, seeds 0-2 | all 338 | 3 |
| **B** sampling on | the sampled tokens | temperature 0.7, seeds 1-5 | all 338 | 5 |
| **C** re-presented part | the order the key facts are listed in (5 seeded random orders) | temperature 0, seed 0 | reference answers whose question has 2 or more key facts | 5 |
| **D** short context | the judge's context window: 4,096 tokens instead of 16,384 | temperature 0, seed 0 | all 338 | 1 |

Why these: the judge was registered at temperature 0, so repeating identical requests (A) mostly checks that
"deterministic" holds, including across machines (A's first trial against the existing laptop grades). C is the real
repeatability test for a deterministic gauge: present the same part again in a way that should not matter. B shows what
a default sampling temperature would cost. See `docs/why-not-just-temperature-zero.md`.

Arm D was added while preparing this protocol, before any study grading. Ollama chooses a default context window from
the GPU's memory; on the machine prepared for this study it chose 16,384 tokens, and a 16 GB GPU may get 4,096. The
original runs did not record theirs. v1 cites whole pages: 23 of its 169 cited sources are longer than about 3,000
tokens, and none of v2's are. If the original judge's context was short, long v1 sources would have been cut off, which
would look exactly like "the judge misses support in v1's citations". **Hypothesis, stated in advance:** on v1 answers
with long sources, arm D fails support more often than arm A's first trial, and arm D agrees with the existing laptop
grades better than arm A does. The original setting will also be read from the laptop when it is next switched on.

Within each trial the parts are graded in a seeded random order. Gradings that end in a judge error (no parsable
reply after retries) are retried on resume; any that remain are dropped and counted.

## Measures

The verdict analysed is LLM-chatbot's headline, **"correct and supported"** (`primary`), as pass/fail. `correct`
alone is reported as a secondary table. Questions whose grade is partly mechanical (exact-match answers) or of a
different kind (unanswerable) are included in the headline and also shown separately.

Statistics are those of the judge-msa package (README, "What is reported"): within-judge agreement and flip rate per
arm; agreement between judges (pairwise Cohen's kappa, Fleiss' kappa); each judge against the reference (agreement,
kappa, miss rate, false-alarm rate), by system; bias by system and its difference between systems; variance components;
and the minimum resolvable difference (MRD) for v2 against v1, per judge, at the study's 169 questions. Intervals are
95% percentile bootstrap, resampling questions, 2,000 draws, seed 0.

## How the result will be read

No pass/fail threshold is set for the judges. The report places each judge's MRD beside the v2-v1 difference that
judge reports and says which is larger, and it separates the part of the MRD that more trials would shrink (noise)
from the part they would not (bias between systems). Conventional kappa guides (above 0.75 good, below 0.40 poor) are
quoted as context only.

Expectations written down in advance: arm A will show near-perfect repeatability; arm C will show some verdicts moving
with key-fact order; the judges' bias will be less favourable to v1 than to v2; and the MRD will be dominated by bias,
not noise.

## Reference repeatability

The grader will blind-regrade 30 of the 100 reference answers (stratified by system and by his first verdict, new
random codes, earlier grades hidden). His two gradings are analysed as two trials of a fourth appraiser. Until that is
done the reference's own repeatability is unmeasured, and the report says so.

## Limits known in advance

One human grader; three manuals; one judge prompt; 50 reference questions, 21 of them chosen for being disputed; the
new runs use a different machine and Ollama version from the original ones.

## Deviations

None yet.
