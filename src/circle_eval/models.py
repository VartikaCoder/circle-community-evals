from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class Turn:
    user: str
    assistant: str = ""
    plan: list[ToolCall] = field(default_factory=list)
    executed: list[ToolCall] = field(default_factory=list)
    answer: Any = None
    latency_ms: float = 0.0
    cost_usd: float = 0.0


@dataclass(frozen=True)
class Scenario:
    id: str
    community_id: str
    turns: tuple[str, ...]
    expected_answer: Any
    expected_tools: tuple[ToolCall, ...]
    description: str
