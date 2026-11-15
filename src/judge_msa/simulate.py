"""Simulate verdict tables with planted judge behaviour, to validate the estimators.

Model: each part (item, system) has a true outcome t ~ Bernoulli(p_system); the reference equals t.
A judge holds a persistent latent verdict L per part: L = 1 with probability 1 - false_alarm when
t = 1, and with probability miss when t = 0. Each trial reports L flipped with probability flip.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from judge_msa.table import validate

PASS, FAIL = "pass", "fail"


@dataclass(frozen=True)
class JudgeSpec:
    flip: float = 0.0
    miss: float | dict[str, float] = 0.0
    false_alarm: float | dict[str, float] = 0.0

    def miss_for(self, system: str) -> float:
        return self.miss[system] if isinstance(self.miss, dict) else self.miss

    def false_alarm_for(self, system: str) -> float:
        return self.false_alarm[system] if isinstance(self.false_alarm, dict) else self.false_alarm


def expected(spec: JudgeSpec, system: str, p: float) -> dict[str, float]:
    """Planted values for one judge and system: expected score, bias and repeatability variance."""
    q = p * (1 - spec.false_alarm_for(system)) + (1 - p) * spec.miss_for(system)
    score = q * (1 - spec.flip) + (1 - q) * spec.flip
    return {"score": score, "bias": score - p, "rep_var": spec.flip * (1 - spec.flip)}


def simulate(
    n_items: int,
    systems: dict[str, float],
    judges: dict[str, JudgeSpec],
    n_trials: int,
    *,
    ref_fraction: float = 1.0,
    seed: int = 0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    items = np.array([f"q{i:05d}" for i in range(n_items)])
    has_ref = np.zeros(n_items, dtype=bool)
    has_ref[rng.permutation(n_items)[: round(ref_fraction * n_items)]] = True
    frames = []
    for system, p in systems.items():
        truth = rng.random(n_items) < p
        ref = np.where(has_ref, np.where(truth, PASS, FAIL), None)
        for judge, spec in judges.items():
            p_latent = np.where(truth, 1 - spec.false_alarm_for(system), spec.miss_for(system))
            latent = rng.random(n_items) < p_latent
            for trial in range(n_trials):
                y = latent ^ (rng.random(n_items) < spec.flip)
                frames.append(
                    pd.DataFrame(
                        {
                            "item": items,
                            "system": system,
                            "judge": judge,
                            "trial": trial,
                            "verdict": np.where(y, PASS, FAIL),
                            "reference": ref,
                        }
                    )
                )
    return validate(pd.concat(frames, ignore_index=True))
