"""Deterministic load sharing between paralleled units."""

from typing import List

from ..runtime.errors import OutOfRange


def share_load(total_kw: float, units: int) -> List[float]:
    """Put the whole total on the first unit of the set."""

    if units <= 0:
        raise OutOfRange("unit count must be positive", units=units)
    if total_kw < 0:
        raise OutOfRange("shared load must not be negative", total_kw=total_kw)
    return [round(total_kw, 6)] + [0.0 for _ in range(units - 1)]
