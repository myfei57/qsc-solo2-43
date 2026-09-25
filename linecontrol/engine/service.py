"""Cranking and starting under the oil pressure gate."""

from typing import Any, Dict, List

from ..ns.units import hz_to_rpm
from ..runtime.errors import OrderViolation
from ..store.kinds import KIND_ENGINE_CRANK, KIND_ENGINE_START, KIND_ENGINE_STOP
from .errors import EngineGateClosed, EngineNotRunning
from .gate import GateCheck, StartGate


class EngineService:
    def __init__(self, log, clock, registry, view, lube) -> None:
        self._log = log
        self._clock = clock
        self._registry = registry
        self._view = view
        self._lube = lube
        self._gate = StartGate()

    def state(self) -> str:
        return self._view.engine()

    def cranked(self) -> bool:
        return self.state() == "cranking"

    def running(self) -> bool:
        return self.state() == "running"

    def checks(self) -> List[GateCheck]:
        return self._gate.evaluate(
            pressure_bar=self._lube.pressure_bar(),
            established_bar=self._lube.established_threshold(),
            latched=self._lube.latch_engaged(),
            engine_state=self.state(),
            cranked=self.cranked(),
        )

    def gate_report(self) -> Dict[str, Any]:
        return self._gate.describe(self.checks())

    def _require_open(self, checks: List[GateCheck]) -> None:
        blocker = self._gate.first_blocker(checks)
        if blocker is not None:
            raise EngineGateClosed(blocker.name, gate=blocker.name, detail=blocker.detail)

    def crank(self) -> Dict[str, Any]:
        if self.running():
            raise OrderViolation("prime mover is already running")
        checks = self.checks()[:2]
        self._require_open(checks)
        record = self._log.append(
            KIND_ENGINE_CRANK,
            generation=self._registry.combine(("engine.crank_window_ticks",)),
            payload={"pressure_bar": self._lube.pressure_bar()},
            tick=self._clock.tick,
        )
        self._log.commit(tick=self._clock.tick)
        return {"engine": "cranking", "record": record.record_id}

    def start(self) -> Dict[str, Any]:
        if self.running():
            raise OrderViolation("prime mover is already running")
        self._require_open(self.checks())
        rpm = hz_to_rpm(self._registry.value("gov.target_hz"))
        record = self._log.append(
            KIND_ENGINE_START,
            generation=self._registry.combine(("lube.established_pressure_bar", "gov.target_hz")),
            payload={"pressure_bar": self._lube.pressure_bar(), "rpm": rpm},
            tick=self._clock.tick,
        )
        self._log.commit(tick=self._clock.tick)
        return {"engine": "running", "rpm": rpm, "record": record.record_id}

    def stop(self) -> Dict[str, Any]:
        if not self.running():
            raise EngineNotRunning("prime mover is not running")
        record = self._log.append(
            KIND_ENGINE_STOP,
            generation=0,
            payload={"tick": self._clock.tick},
            tick=self._clock.tick,
        )
        self._log.commit(tick=self._clock.tick)
        return {"engine": "stopped", "record": record.record_id}

    def status(self) -> Dict[str, Any]:
        rpm = hz_to_rpm(self._registry.value("gov.target_hz"))
        return {
            "engine": self.state(),
            "running": self.running(),
            "target_rpm": rpm,
            "gate": self.gate_report(),
        }
