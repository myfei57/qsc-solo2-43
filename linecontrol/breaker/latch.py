"""Trip latch release policy."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LatchReleaseDecision:
    releasable: bool
    reason: str

    def describe(self) -> Dict[str, Any]:
        return {"releasable": self.releasable, "reason": self.reason}


class LatchReleasePolicy:
    """A trip latch is released once the breaker is off the line."""

    def __init__(self, load_tolerance_kw: float = 0.0) -> None:
        self._tolerance = float(load_tolerance_kw)

    def decide(self, breaker_state: str, load_kw: float) -> LatchReleaseDecision:
        if breaker_state != "open":
            return LatchReleaseDecision(False, "breaker must be open before the latch is released")
        return LatchReleaseDecision(True, "release conditions satisfied")

    def describe(self) -> Dict[str, Any]:
        return {"load_tolerance_kw": self._tolerance}
