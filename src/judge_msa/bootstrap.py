"""Percentile bootstrap that resamples items (clusters), so parts sharing an item move together."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

DEFAULT_N_BOOT = 2000


def bootstrap_items(
    n_items: int,
    stat: Callable[[np.ndarray], float],
    *,
    n_boot: int = DEFAULT_N_BOOT,
    seed: int = 0,
    level: float = 0.95,
) -> tuple[float, float]:
    """Interval for ``stat``, a function of an array of item positions (with repeats)."""
    rng = np.random.default_rng(seed)
    draws = np.array([stat(rng.integers(0, n_items, n_items)) for _ in range(n_boot)], dtype=float)
    draws = draws[~np.isnan(draws)]
    if len(draws) == 0:
        return (float("nan"), float("nan"))
    alpha = (1 - level) / 2
    lo, hi = np.quantile(draws, [alpha, 1 - alpha])
    return (float(lo), float(hi))
