"""Current rotation from CDL crop history + choice of 3 alternatives from params.CATALOGUE."""

from __future__ import annotations

from collections import Counter

from engine import params

RECENT_YEARS = 8  # how much CDL history defines "current"
MAX_PERIOD = 5
MAX_MISMATCH = 0.25  # share of recent years allowed to break the detected cycle


def detect_rotation(crop_history: dict[str, str], recent: int = RECENT_YEARS) -> list[str]:
    """Shortest repeating crop cycle that explains the last ``recent`` CDL years.

    Tries cycle lengths 1..MAX_PERIOD and keeps the shortest whose cycle mismatches at most
    MAX_MISMATCH of the years. The cycle is returned in the order of the most recent years.
    Falls back to the last 4 observed years when nothing repeats.
    """
    years = sorted(crop_history, key=int)[-recent:]
    seq = [crop_history[y] for y in years]
    n = len(seq)
    for period in range(1, min(MAX_PERIOD, n) + 1):
        # majority crop at each position of the cycle, aligned so the last year is position -1
        cycle = []
        mismatches = 0
        for pos in range(period):
            members = [seq[i] for i in range(n) if (n - 1 - i) % period == period - 1 - pos]
            crop, count = Counter(members).most_common(1)[0]
            cycle.append(crop)
            mismatches += len(members) - count
        if mismatches / n <= MAX_MISMATCH:
            return cycle
    return seq[-4:]


def _signature(rotation: list[str] | tuple[str, ...], irrigation: str) -> dict[str, float]:
    """Crop shares + irrigation level as a feature vector for distances."""
    shares = Counter(rotation)
    vec = {c: k / len(rotation) for c, k in shares.items()}
    level = {"full": 1.0, "limited": 0.5, "dryland": 0.0}[irrigation]
    vec["__irrigation__"] = level
    return vec


def distance(a: dict[str, float], b: dict[str, float]) -> float:
    """Half-L1 distance between crop-share vectors plus half the irrigation difference."""
    keys = (set(a) | set(b)) - {"__irrigation__"}
    crops = 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)
    return crops + 0.5 * abs(a["__irrigation__"] - b["__irrigation__"])


def select_alternatives(
    current: list[str], current_irrigation: str, irrigated: bool = True, n: int = 3
) -> list[tuple[params.CatalogueEntry, str]]:
    """Pick ``n`` (catalogue entry, irrigation level) pairs that differ from the current
    rotation and from each other (greedy farthest-point, ties -> catalogue order).
    On non-irrigated fields every option is evaluated as dryland."""
    cur = _signature(current, current_irrigation)
    pool: list[tuple[params.CatalogueEntry, str]] = []
    seen = set()
    for e in params.CATALOGUE:
        level = e.irrigation if irrigated else "dryland"
        key = (e.rotation, level)
        if key in seen or distance(_signature(e.rotation, level), cur) == 0:
            continue
        seen.add(key)
        pool.append((e, level))
    chosen: list[tuple[params.CatalogueEntry, str]] = []
    sigs = [cur]
    while pool and len(chosen) < n:
        best = max(pool, key=lambda c: min(distance(_signature(c[0].rotation, c[1]), s)
                                           for s in sigs))  # fmt: skip
        chosen.append(best)
        sigs.append(_signature(best[0].rotation, best[1]))
        pool.remove(best)
    return chosen
