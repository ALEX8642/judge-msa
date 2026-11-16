# Worked study: the judges of LLM-chatbot

[LLM-chatbot](https://github.com/ALEX8642/LLM-chatbot) reported that its v2 pipeline answered 80% of a registered test
correctly and with support, against 42% for v1, as graded by a local LLM judge. Blind human grading then showed the
judge was harder on v1's citations on a set of disputed answers. This study treats the judges as gauges and asks how
far their verdicts can be trusted. The [protocol](protocol.md) was committed before any new grading; its deviations
and the outcome of each advance statement are logged at its end.

**In one paragraph.** The judges are repeatable (identical verdicts on 99.7 to 100% of answers at temperature 0) and
agree with each other on 90% of answers. Against the human reference they are about 2 to 9 points off per system, and
the difference in that bias between v2 and v1 is small but poorly pinned down: the reference has only 29 randomly
drawn questions, so each judge can resolve a v2-v1 difference only above about **19 to 21 points**. The reported
differences (30 to 37 points) are larger than that. The much-quoted judge bias against v1 is real on the answers that
were picked for being disputed and is not visible on the randomly drawn ones. Two things nobody had controlled turned
out to move verdicts: the order in which key facts are listed in the prompt, and the judge server's context window.

## What was run

- **Parts:** 338 answers (169 test questions × v1, v2), fixed.
- **Judges:** phi4:14b and mistral-small3.2:24b (the registered ones) and gemma3:27b, all with LLM-chatbot's grader
  and judge prompt unchanged.
- **Reference:** one person's blind grades of 100 of the answers; 21 questions chosen because a judge disputed them,
  29 drawn at random. Reference statistics are weighted for that.
- **9,996 gradings** in four arms on one RTX 5090. 39 ended in an unusable reply after retries and were dropped.

| Arm | Between trials, what changes | gemma3 | mistral | phi4 |
|---|---|---|---|---|
| A: temperature 0, 3 trials, all answers | nothing | 100% identical | 100% | 99.7% |
| B: temperature 0.7, 5 trials, all answers | sampling | flip rate 0.3% | 3.1% | 6.0% |
| C: temperature 0, key facts in 5 random orders, 58 answers | presentation | 6.9% of answers change verdict | 6.9% | 6.9% |
| D: temperature 0, context 4,096 instead of 16,384 tokens | server setting | 1 of 338 verdicts change | 4 | 3 |

Flip rate is the chance that two trials of one answer disagree. Reports: [arm A](reports/arm-A/report.md),
[B](reports/arm-B/report.md), [C](reports/arm-C/report.md), [D](reports/arm-D/report.md),
[the original laptop grades](reports/existing/report.md); the same without sampling weights in
[existing-unweighted](reports/existing-unweighted/report.md). Raw gradings are in `data/`.

## Findings

**1. Repeatable is not the same as right.** Arm A is as repeatable as a gauge gets. The same judges, on the same
answers, miss or falsely fail a noticeable share against the reference: on v1, phi4 and mistral fail 37 to 39% of the
answers the human passed; on v2, 7%.

**2. A deterministic judge still reacts to presentation.** Listing the same key facts in a different order changed the
verdict on 4 of 58 answers for every judge, at temperature 0. Repeating an identical request cannot reveal this.
(58 answers is a small sample; read 6.9% as "a few percent", not as a precise rate.)

**3. Judges agree with each other more than with the human.** All three judges give the same verdict on every trial
for 90% of answers (Fleiss' kappa 0.86). Against the human, kappa on v1 answers is 0.45 for phi4 and mistral and
0.65 for gemma3. Agreement between judges is not evidence that they are right: they can share a blind spot.

**4. What each judge can resolve.** For v2 against v1 on 169 questions:

| Judge | Reported v2 − v1 | Noise | Bias bound | Minimum resolvable difference |
|---|---|---|---|---|
| gemma3:27b | +30.3 points | 0.0 | 21.1 | 21.1 points |
| mistral-small3.2:24b | +32.5 | 0.0 | 19.4 | 19.4 |
| phi4:14b | +37.4 | 0.4 | 19.8 | 20.2 |

Nearly all of it is the bias bound: how different the judge's bias on v2 and on v1 could be, given the reference.
More judge trials would not shrink it. More randomly drawn reference questions would. v2's lead clears the bar for
every judge; a difference of 10 or 15 points would not have, and nothing in the original eval would have said so.

**5. The bias against v1 depends on which answers you look at.** Estimated for the whole test, the difference in bias
between v2 and v1 is +4.5 points for phi4 (95% interval −12 to +20), +1.8 for mistral and −6.0 for gemma3: no clear
bias either way. On the enriched sample taken as it stands, phi4's figure is +20 points (interval +2 to +38), which is
what triggered LLM-chatbot's judge-validity warning. On the 21 disputed questions phi4 scores 44 points below the
human; on the 29 random ones, 2 points below. A reference set built from disputed cases shows the judge at its worst.

**6. An uncontrolled setting was part of the measurement.** Ollama picks a default context window from the GPU's
memory. On the 5090 it chose 16,384 tokens. Run again at 4,096 tokens, both registered judges reproduce the original
laptop verdicts on all 23 answers with long cited sources (20 and 21 of 23 at 16,384), and mistral reproduces all 338
original verdicts. The original runs therefore very probably used 4,096 tokens, which nobody chose or wrote down, and
which cuts off v1's longest cited pages. The advance guess that this *caused* the bias against v1 did not hold: the
shorter context changed verdicts in both directions. (The laptop's actual setting is still to be read from it.)

**7. Temperature 0 did not make the judge reproducible across machines.** With the context window matched, phi4 on
the 5090 still differs from phi4 on the laptop on 5 of 337 answers.

**8. One candidate judge could not follow the reply format.** gemma3:27b answered the key-fact prompt in a different
JSON shape on 54% of its gradings, which LLM-chatbot's parser reads as an error. The content was unambiguous, so the
study merged those replies (protocol deviation 2) and marked them. As delivered, gemma3 with this prompt is not a
usable judge, however sensible its verdicts are once parsed.

## Limits

- One human grader, not a subject expert. His own repeatability is being measured by a blind regrade of 30 answers
  (not yet in these figures); until then the bias figures rest on a reference of unknown stability.
- 50 reference questions, 29 of them random. That is why the bias bound is wide.
- Three manuals, one judge prompt, one question set. Nothing here says how these judges behave elsewhere.
- The new runs used a different machine and Ollama version from the original.
- The minimum resolvable difference is conservative by construction (see `docs/validation.md`).

## Reproducing

```
python build_table.py --llm-chatbot PATH            # data/existing.csv from LLM-chatbot's results
./run.sh --llm-chatbot PATH --arm A --judge phi4:14b --out data/trials-A.jsonl   # needs an OpenAI-compatible judge
python build_table.py --llm-chatbot PATH --arm A    # data/arm-A.csv
judge-msa analyze data/arm-A.csv --system system --reference reference --weight weight \
    --positive pass --compare v2 v1 --by category selected --out reports/arm-A
```
