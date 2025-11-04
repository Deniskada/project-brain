from __future__ import annotations

from typing import Dict


DEFAULT_ROLE_WEIGHTS: Dict[str, float] = {
    "owner": 0.9,
    "manager": 0.8,
    "employee": 0.6,
    "admin": 0.7,
    "moderator": 0.5,
    "system": 0.4,
}

# Can be overridden dynamically at runtime via storage layer
DEFAULT_SUBSYSTEM_WEIGHTS: Dict[str, float] = {}


def normalize(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.0
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def compute_weight(
    role: str,
    subsystem: str,
    degree_in: int,
    degree_out: int,
    role_weights: Dict[str, float] | None = None,
    subsystem_weights: Dict[str, float] | None = None,
    max_degree: int = 1,
) -> float:
    role_w = (role_weights or DEFAULT_ROLE_WEIGHTS).get(role, 0.4)
    subs_w = (subsystem_weights or DEFAULT_SUBSYSTEM_WEIGHTS).get(subsystem, 0.5)
    connections = degree_in + degree_out
    conn_norm = normalize(connections, 0, max_degree)
    return round(role_w * 0.4 + subs_w * 0.3 + conn_norm * 0.3, 6)


