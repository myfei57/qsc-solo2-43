"""Frequency adjustment for the closed breaker."""

from typing import Any, Dict

from ..ns.units import hz_to_rpm
from ..store.kinds import KIND_GOV_ADJUST
from .errors import GovernorGateClosed


class GovernorService:
    def __init__(self, log, clock, registry, view, tickets, breaker_closed) -> None:
        self._log = log
        self._clock = clock
        self._registry = registry
        self._view = view
        self._tickets = tickets
        self._breaker_closed = breaker_closed

    def target_hz(self) -> float:
        return self._view.target_hz()

    def adjust(self, target_hz: float, ticket_id: str) -> Dict[str, Any]:
        if not self._breaker_closed():
            raise GovernorGateClosed("the governor adjusts only after the breaker closes")
        setting = self._registry.value("gov.target_hz")
        record = self._log.append(
            KIND_GOV_ADJUST,
            generation=self._registry.generation("gov.target_hz"),
            payload={"target_hz": round(setting, 6), "rpm": hz_to_rpm(setting)},
            tick=self._clock.tick,
        )
        self._log.commit(tick=self._clock.tick)
        return {
            "target_hz": round(setting, 6),
            "rpm": hz_to_rpm(setting),
            "record": record.record_id,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "target_hz": self.target_hz(),
            "rpm": hz_to_rpm(self.target_hz()),
        }
