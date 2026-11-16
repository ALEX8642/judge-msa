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
  A human **pass** is scored as LLM-chatbot scored it (this reproduces its published 42 of 50 for v2 and 31 of 50
  for v1): on an answerable question, graded "correct" with the cited pages showing it; on an unanswerable question,
  a decline. "Partly", "wrong", unsupported, declines on answerable questions and answers to unanswerable ones fail.
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

1. 2026-11-15, before any analysis and while arm A was running: the human pass rule was first written as "a decline
   on an unanswerable question passes, and so does a correct, supported answer on any question". That gave 44 and 35
   passes, not LLM-chatbot's published 42 and 31. The published scoring fails an *answer* to an unanswerable question
   even when graded correct; the rule above was corrected to match it. Judge runs are unaffected.
2. 2026-11-15, after the first pass of arms A-C, before any analysis of them: gemma3:27b answered the key-fact prompt
   with a JSON array of one object per key fact, where the prompt asks for one object holding a list, on about half of
   its gradings (always the same questions, those with two or more key facts in certain layouts). LLM-chatbot's parser
   reads only the first object, so these counted as judge errors. The reply's content is unambiguous, so the driver
   now merges such arrays (`merge_per_fact_objects` in `rejudge.py`) and marks the grading `merged_reply`. The errored
   gradings were re-run with the merge. The share of merged replies is reported per judge: a judge that does not
   follow the reply format is a finding about the measurement system, not something to hide. phi4 and mistral are
   unaffected by the merge unless they produce the same shape.
   Added the same day, during the re-run: gemma3 also uses a second array shape, a bare list of
   `{"fact", "present"}` objects with no "abstained" field. It is merged the same way with abstained taken as false,
   which cannot change the correctness verdict (all facts present means the answer committed; any fact absent means
   it is wrong either way). The judge's separate "abstained" flag is therefore not analysed for merged gradings.

## Results noted against the advance statements (2026-11-15)

- **Arm A, near-perfect repeatability:** held. gemma3 and mistral 100% identical over 3 trials, phi4 99.7%.
- **Arm C, some verdicts move with key-fact order:** held. 6.9% of the 58 answers changed verdict across 5 orders,
  for each of the three judges.
- **Arm D hypothesis, part 1** (at a 4,096-token context, v1's long-source answers fail more often): **did not hold.**
  On the 23 v1 answers with long sources, passes went from 14 to 11 for mistral but from 9 to 11 for phi4 and from 14
  to 15 for gemma3. The context window changes verdicts on long sources (3, 2 and 1 of 23), in no consistent
  direction. It does not explain the judges' harsher treatment of v1.
- **Arm D hypothesis, part 2** (the 4,096-token run matches the laptop grades better than the 16,384-token run):
  **held.** On those 23 answers the 4,096-token run reproduces the laptop's verdicts 23 of 23 for both registered
  judges, against 20 and 21 of 23 at 16,384 tokens. Overall it matches the laptop on 338 of 338 answers for mistral
  and 332 of 337 for phi4. The original runs therefore very probably used a 4,096-token context, a setting nobody
  chose or recorded. **Confirmed on the laptop 2026-11-15:** Ollama 0.40.15, no `OLLAMA_CONTEXT_LENGTH` set, and
  both registered judges load with a 4,096-token context (same model digests as in this study). The laptop's Ollama
  version at the time of the original runs was not recorded.
- **Same judge, same settings, different machine:** phi4 still differs on 5 of 337 answers with the context matched.
- **Reference repeatability** (regrade done 2026-11-15, 30 answers): same pass/fail verdict on 29 of 30, kappa 0.93;
  same raw grade on 23 of 30, kappa 0.63.
