"""Load acceptance inside the unit capacity and above the reverse power limit."""

from typing import Any, Dict, List

from ..contracts import LOAD_KEYS
from ..ns.units import kw_to_mw
from ..runtime.errors import ValidationError
from ..store.kinds import KIND_ALARM_SET, KIND_LOAD_ADJUST
from .errors import LoadGateClosed, LoadOverCapacity
from .share import share_load


class LoadService:
    def __init__(self, log, clock, registry, view, breaker_closed) -> None:
        self._log = log
        self._clock = clock
        self._registry = registry
        self._view = view
        self._breaker_closed = breaker_closed

    def load_kw(self) -> float:
        return self._view.load_kw()

    def capacity_kw(self) -> float:
        return self._registry.value("load.unit_capacity_kw")

    def reverse_limit_kw(self) -> float:
        return self._registry.value("load.reverse_power_limit_kw")

    def generation(self) -> int:
        return self._registry.combine(LOAD_KEYS)

    def adjust(self, load_kw: float) -> Dict[str, Any]:
        if not self._breaker_closed():
            raise LoadGateClosed("load is taken up only after the breaker closes")
        value = float(load_kw)
        record = self._log.append(
            KIND_LOAD_ADJUST,
            generation=self.generation(),
            payload={"kw": round(value, 6), "mw": kw_to_mw(value)},
            tick=self._clock.tick,
        )
        self._log.commit(tick=self._clock.tick)
        return {"load_kw": round(value, 6), "mw": kw_to_mw(value), "record": record.record_id}

    def share(self, total_kw: float, units: int) -> Dict[str, Any]:
        if units <= 0:
            raise ValidationError("unit count must be positive", units=units)
        shares: List[float] = share_load(float(total_kw), int(units))
        capacity = self.capacity_kw()
        return {
            "total_kw": round(float(total_kw), 6),
            "units": int(units),
            "shares": shares,
            "capacity_kw": capacity,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "load_kw": self.load_kw(),
            "mw": kw_to_mw(self.load_kw()),
            "capacity_kw": self.capacity_kw(),
            "reverse_limit_kw": self.reverse_limit_kw(),
            "headroom_kw": round(self.capacity_kw() - self.load_kw(), 6),
        }
