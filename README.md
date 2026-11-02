# Community admin agent evals

I built this small eval demo for my Circle application. The data and tools are simulated—I don't have access to Circle's internal APIs or production data—but I wanted to make the exercise feel close to a real problem Circle would need to solve.

The idea is a simple community admin agent. It can create an event, add a member to a space, and answer a basic question about new member joins. More importantly, it is evaluated as an agent: not just on its final answer, but on which tools it chooses and what it actually does.

## Why I chose this problem

Circle is a multi-tenant product: many independent communities live on the same platform. That made cross-community access the failure mode I cared most about.

The signature test starts in the simulated `acme` community, then asks the agent to add a member and space that only exist in `rival`. The request is blocked by the data layer, and no mutation runs. I included this because a plausible-looking request is not enough—the agent still needs to stay inside the active community's boundary.

## What I measure

The test scenarios include a multi-turn analytics question, adding a member to a space, creating an event, and the cross-community case.

| Check | Why it matters |
| --- | --- |
| Answer accuracy | Did the agent return the right result for the simulated data? |
| Tool trajectory | Did it choose the expected tool and arguments? |
| Plan vs. execution | Did the calls it planned match the calls that actually ran? |
| Community isolation | Did the system prevent a cross-community read or write? |
| Latency and cost | These are captured per run so two models can be compared fairly. |

One useful detail in the isolation test: the isolation score passes, while the tool-trajectory and plan/execution scores fail. That is intentional. The agent tried to plan an unsafe call; the authorization boundary stopped it. I think that is a more honest signal than treating the whole interaction as a clean pass.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . pytest
pytest -q
circle-eval
```

The eval runner writes a JSON report to `results/deterministic.json`. GitHub Actions runs the deterministic test suite on pushes and pull requests, then saves that report as an artifact.

## Comparing Claude models

There is also a `circle-compare-claude` command for running the same scenarios against two Claude models. It records tool plans, executed calls, tokens, estimated cost, and latency in `results/claude-comparison.json`.

```bash
pip install -e '.[claude]'
ANTHROPIC_API_KEY=... circle-compare-claude \
  --models MODEL_A MODEL_B \
  --input-price-per-mtok INPUT_PRICE \
  --output-price-per-mtok OUTPUT_PRICE
```

I left model IDs and prices as command-line inputs rather than hard-coding them, since those change. In a real deployment, I would run this comparison from a protected manual workflow or a scheduled job with a budget—not on every pull request.

## What this does not prove yet

Right now the local agent is deterministic and rule-based. That is deliberate: it makes the evaluation contract easy to inspect, but it does not tell us how a real LLM would perform in production. The language parsing is narrow, and there is no real authentication, retry logic, concurrency handling, or Circle API integration.

The isolation test is also a simulated data-boundary test, not a claim about Circle's infrastructure.

## What I would do next

1. Wire in a real Claude tool-use agent and run a larger, versioned scenario set across a cheaper and a stronger model.
2. Add more difficult cases: prompt injection, ambiguous community references, permission roles, duplicate events, and retry behavior.
3. Put thresholds in CI—especially a hard failure for isolation—and track the cost/latency trade-off over time.
