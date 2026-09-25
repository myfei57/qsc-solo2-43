"""The ordered gate that guards cranking and starting."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GateCheck:
    name: str
    passed: bool
    detail: Dict[str, Any] = field(default_factory=dict)

    def describe(self) -> Dict[str, Any]:
        return {"gate": self.name, "passed": self.passed, "detail": dict(self.detail)}


class StartGate:
    """Preconditions are evaluated in order; the first failure blocks the step."""

    def evaluate(
        self,
        pressure_bar: float,
        established_bar: float,
        latched: bool,
        engine_state: str,
        cranked: bool,
    ) -> List[GateCheck]:
        return [
            GateCheck(
                "oil.pressure.established",
                pressure_bar >= established_bar,
                {"pressure_bar": pressure_bar, "required_bar": established_bar},
            ),
            GateCheck("oil.latch.clear", not latched, {"latched": latched}),
            GateCheck("crank.complete", cranked, {"engine": engine_state}),
        ]

    def first_blocker(self, checks: List[GateCheck]) -> Optional[GateCheck]:
        for check in checks:
            if not check.passed:
                return check
        return None

    def describe(self, checks: List[GateCheck]) -> Dict[str, Any]:
        blocker = self.first_blocker(checks)
        return {
            "checks": [check.describe() for check in checks],
            "open": blocker is None,
            "blocked_by": blocker.name if blocker else "",
        }
