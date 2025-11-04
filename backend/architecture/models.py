from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Node:
    id: str
    label: str
    type: str  # role | subsystem | function | task
    role: Optional[str] = None
    subsystem: Optional[str] = None
    file: Optional[str] = None
    lines: Optional[str] = None
    fqn: Optional[str] = None
    weight: float = 0.0
    degree_in: int = 0
    degree_out: int = 0
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    type: str  # calls | belongs_to | part_of | relates_to


@dataclass
class GraphData:
    nodes: List[Node]
    edges: List[Edge]
    stats: Dict[str, int]


