from circle_eval.agent import CommunityAdminAgent
from circle_eval.evaluators import score_turn
from circle_eval.scenarios import ISOLATION_SCENARIO, SCENARIOS
from circle_eval.store import CommunityStore


def test_happy_path_scenarios_score_perfectly():
    for scenario in SCENARIOS:
        agent = CommunityAdminAgent(CommunityStore())
        for message in scenario.turns[:-1]:
            agent.respond(message, scenario.community_id)
        turn = agent.respond(scenario.turns[-1], scenario.community_id)
        score = score_turn(turn, scenario)
        assert (score.accuracy, score.tool_trajectory, score.plan_execution_match) == (1.0, 1.0, 1.0)


def test_cross_community_request_is_rejected_without_a_tool_execution():
    scenario = ISOLATION_SCENARIO
    turn = CommunityAdminAgent(CommunityStore()).respond(scenario.turns[-1], scenario.community_id)
    score = score_turn(turn, scenario, isolation=True)
    assert score.isolation == 1.0
    assert not turn.executed
