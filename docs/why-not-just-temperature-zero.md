# "The judge ran at temperature 0. Why does it need a Gage R&R?"

The judges in the worked study (LLM-chatbot) ran at temperature 0 with a fixed seed. That is a fair reason to ask
whether a measurement system analysis has anything left to measure. It does, for five reasons.

**1. Temperature 0 removes one source of variation out of three.** A measurement system analysis asks about
*repeatability* (same gauge, same part, again), *reproducibility* (a different gauge or operator, same part) and
*bias* (the gauge against a reference). Temperature 0 addresses part of the first. It says nothing about the other two.

**2. A repeatable gauge can be repeatably wrong.** Precision is not accuracy. LLM-chatbot's own blind human grading
found the registered judge was harder on one system's citation style than the other's, enough to turn a level result
into an apparent win. At temperature 0 that bias is perfectly stable: running the judge again, or on more questions,
never averages it out. A noisy gauge can be improved by repeating the measurement. A biased one cannot.

**3. Two judges at temperature 0 still disagree with each other.** The two registered judges, given the same answers
and the same prompt, reported different leads for the same comparison. That is reproducibility, and temperature has no
bearing on it.

**4. Sending the identical prompt twice is not a repeatability test.** A caliper also reads the same if the part never
leaves its jaws. A gauge study takes the part out and puts it back, because the variation that matters comes from
re-presenting the part. For an LLM judge the equivalent is a change that should make no difference to the verdict: the
order in which the key facts are listed, for example. If the verdict moves, the judge is measuring the presentation as
well as the answer. The study's arm C tests this.

**5. "Deterministic at temperature 0" is a claim to be checked.** The same model at temperature 0 can give different
outputs on different hardware, quantisations or runtime versions. The study's arm A measures this instead of assuming
it, and compares a fresh run on a second machine with the original grades.

Arm B (temperature 0.7) is there for a different audience: many evals run their judge at a default temperature, and
the arm shows what that costs in resolvable difference.

In one line: temperature 0 made the judge consistent; the study asks whether it was right, and whether another judge
would have agreed.
