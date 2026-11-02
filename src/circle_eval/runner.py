from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import CommunityAdminAgent
from .evaluators import score_turn
from .scenarios import ISOLATION_SCENARIO, SCENARIOS
from .store import CommunityStore


def run() -> dict:
    rows = []
    for scenario in (*SCENARIOS, ISOLATION_SCENARIO):
        agent = CommunityAdminAgent(CommunityStore())
        # Preserve transcript shape: earlier turns establish conversational context.
        for message in scenario.turns[:-1]:
            agent.respond(message, scenario.community_id)
        turn = agent.respond(scenario.turns[-1], scenario.community_id)
        score = score_turn(turn, scenario, isolation=scenario.id == "cross-community-isolation")
        rows.append({"id": scenario.id, "score": score.to_dict(), "latency_ms": round(turn.latency_ms, 2), "cost_usd": turn.cost_usd})
    return {"runs": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/deterministic.json")
    args = parser.parse_args()
    report = run()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
