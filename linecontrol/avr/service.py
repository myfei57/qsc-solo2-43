"""Excitation applied to the unit."""

from typing import Any, Dict

from ..ns.units import kw_to_mw
from .errors import ExcitationOrderViolation


class ExcitationService:
    def __init__(self, log, clock, registry, view, engine_running, breaker_closed) -> None:
        self._log = log
        self._clock = clock
        self._registry = registry
        self._view = view
        self._engine_running = engine_running
        self._breaker_closed = breaker_closed
        self._voltage = 0.0

    def voltage(self) -> float:
        return self._voltage

    def nominal_voltage(self) -> float:
        return self._registry.value("avr.excite_voltage_v")

    def excite(self, voltage: float = None) -> Dict[str, Any]:
        value = self.nominal_voltage() if voltage is None else float(voltage)
        self._voltage = round(value, 6)
        return {"voltage": self._voltage}

    def deexcite(self) -> Dict[str, Any]:
        if self.voltage() <= 0:
            raise ExcitationOrderViolation("excitation is already removed")
        self._voltage = 0.0
        return {"voltage": 0.0}

    def status(self) -> Dict[str, Any]:
        return {
            "voltage": self.voltage(),
            "load_mw": kw_to_mw(self._view.load_kw()),
        }
