"""Small, dependency-free statistics. Everything is deterministic (seeded) so a decision can be replayed."""
from __future__ import annotations

import hashlib
import math

import numpy as np


def norm_sf(z: float) -> float:
    """P(Z > z) for standard normal."""
    return 0.5 * math.erfc(z / math.sqrt(2))


def z_two_prop(y1: float, n1: float, y2: float, n2: float) -> float:
    """z for H1: p1 > p2 (pooled variance). 0 if either side is empty."""
    if n1 <= 0 or n2 <= 0:
        return 0.0
    p = (y1 + y2) / (n1 + n2)
    se = math.sqrt(max(p * (1 - p) * (1 / n1 + 1 / n2), 1e-12))
    return (y1 / n1 - y2 / n2) / se


def wilson(y: float, n: float, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 1.0
    p = y / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def binom_upper_p(k: int, n: int, p0: float) -> float:
    """Exact one-sided P(X >= k | n, p0)."""
    if k <= 0:
        return 1.0
    if p0 <= 0:
        return 0.0
    lp, lq = math.log(p0), math.log1p(-p0)
    terms = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq
             for i in range(k, n + 1)]
    m = max(terms)
    return min(1.0, math.exp(m) * sum(math.exp(t - m) for t in terms))


def ratio_ci(y1, n1, y2, n2, z=1.96) -> tuple[float, float, float]:
    """Ratio of two proportions p1/p2 with a log-scale (Katz) CI."""
    if n1 <= 0 or n2 <= 0 or y2 <= 0:
        return 0.0, 0.0, float("inf")
    p1, p2 = max(y1, 0.5) / n1, y2 / n2
    r = p1 / p2
    se = math.sqrt(max(1 / max(y1, 0.5) - 1 / n1 + 1 / y2 - 1 / n2, 1e-12))
    return r, r * math.exp(-z * se), r * math.exp(z * se)


def seed_of(*parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "little")


def prob_best(a: list[float], b: list[float], seed: int, draws: int = 20000) -> list[float]:
    """P(arm i has the highest rate) under independent Beta(a_i, b_i) posteriors. Seeded => deterministic."""
    rng = np.random.default_rng(seed)
    s = np.stack([rng.beta(ai, bi, draws) for ai, bi in zip(a, b)])
    w = np.bincount(s.argmax(axis=0), minlength=len(a))
    return (w / draws).tolist()


def holm(pvals: list[float], alpha: float) -> list[bool]:
    """Holm step-down: which hypotheses are rejected at family-wise level alpha."""
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    rej = [False] * len(pvals)
    m = len(pvals)
    for rank, i in enumerate(order):
        if pvals[i] <= alpha / (m - rank):
            rej[i] = True
        else:
            break
    return rej


def tv(a: dict, b: dict) -> float:
    """Total-variation distance between two {option: weight} maps (normalised)."""
    sa, sb = sum(a.values()) or 1.0, sum(b.values()) or 1.0
    return 0.5 * sum(abs(a.get(k, 0) / sa - b.get(k, 0) / sb) for k in set(a) | set(b))


def normalise(d: dict, nd: int = 3) -> dict:
    s = sum(v for v in d.values() if v > 0)
    out = {k: round(v / s, nd) for k, v in d.items() if v > 0 and round(v / s, nd) > 0}
    # fix rounding so it sums to 1 exactly on the largest weight
    if out:
        top = max(out, key=out.get)
        out[top] = round(out[top] + 1 - sum(out.values()), nd)
    return out
