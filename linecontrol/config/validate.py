"""Type coercion and bound checks for parameter values."""

from typing import Any, Dict

from ..runtime.errors import ValidationError
from .schema import ParameterSpec, spec


def validate_value(target: ParameterSpec, value: Any) -> float:
    if value is None:
        raise ValidationError("parameter value must not be empty", key=target.key)
    return float(value)


def validate_overrides(mapping: Dict[str, Any]) -> Dict[str, float]:
    checked: Dict[str, float] = {}
    for key, value in mapping.items():
        checked[key] = validate_value(spec(key), value)
    return checked
