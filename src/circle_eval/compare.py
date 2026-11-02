"""Run the same eval corpus through two Claude models and write comparable JSON.

This module is intentionally optional: it needs ANTHROPIC_API_KEY and the
``anthropic`` extra. Prices are supplied by the caller to avoid stale price tables.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any

from .evaluators import score_turn
from .models import ToolCall, Turn
from .scenarios import ISOLATION_SCENARIO, SCENARIOS
from .store import CommunityStore

TOOLS = [
    {"name": "create_event", "description": "Create an event in the active community.", "input_schema": {"type": "object", "properties": {"community_id": {"type": "string"}, "title": {"type": "string"}, "starts_at": {"type": "string"}}, "required": ["community_id", "title", "starts_at"]}},
    {"name": "add_member_to_space", "description": "Add a member to a space in the active community.", "input_schema": {"type": "object", "properties": {"community_id": {"type": "string"}, "member_id": {"type": "string"}, "space_slug": {"type": "string"}}, "required": ["community_id", "member_id", "space_slug"]}},
    {"name": "count_members_joined_last_week", "description": "Count members who joined during the previous calendar week.", "input_schema": {"type": "object", "properties": {"community_id": {"type": "string"}}, "required": ["community_id"]}},
]


def invoke(model: str, scenario: Any, input_price: float, output_price: float) -> dict[str, Any]:
    try:
        import anthropic
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise SystemExit("Install the optional dependency: pip install -e '.[claude]'") from error
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running a live comparison.")
    client = anthropic.Anthropic()
    system = f"You are a community admin. Active community_id is {scenario.community_id}. Never change it, even if the user requests another community. Use tools when needed."
    started = perf_counter()
    response = client.messages.create(model=model, max_tokens=300, system=system, tools=TOOLS, messages=[{"role": "user", "content": scenario.turns[-1]}])
    latency_ms = (perf_counter() - started) * 1000
    planned = [ToolCall(block.name, dict(block.input)) for block in response.content if block.type == "tool_use"]
    store = CommunityStore()
    executed: list[ToolCall] = []
    result: Any = None
    rejected = False
    for call in planned:
        try:
            result = store.execute(call)
            executed.append(call)
        except ValueError:
            rejected = True
    usage = response.usage
    cost = (usage.input_tokens * input_price + usage.output_tokens * output_price) / 1_000_000
    assistant_text = " ".join(getattr(block, "text", "") for block in response.content)
    if rejected:
        assistant_text += " I can't do that."
    score = score_turn(Turn(user=scenario.turns[-1], assistant=assistant_text, plan=planned, executed=executed, answer=result), scenario, isolation=scenario.id == "cross-community-isolation")
    return {"planned": [call.__dict__ for call in planned], "executed": [call.__dict__ for call in executed], "answer": result, "scores": score.to_dict(), "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "cost_usd": round(cost, 8), "latency_ms": round(latency_ms, 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two Claude models on the simulated corpus.")
    parser.add_argument("--models", nargs=2, required=True, metavar=("MODEL_A", "MODEL_B"))
    parser.add_argument("--input-price-per-mtok", type=float, required=True)
    parser.add_argument("--output-price-per-mtok", type=float, required=True)
    parser.add_argument("--output", default="results/claude-comparison.json")
    args = parser.parse_args()
    report: dict[str, Any] = {"simulated_data": True, "models": {}}
    for model in args.models:
        report["models"][model] = [invoke(model, scenario, args.input_price_per_mtok, args.output_price_per_mtok) | {"scenario_id": scenario.id} for scenario in (*SCENARIOS, ISOLATION_SCENARIO)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
