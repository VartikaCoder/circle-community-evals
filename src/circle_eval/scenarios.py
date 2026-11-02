from .models import Scenario, ToolCall


SCENARIOS = (
    Scenario(
        id="weekly-joins-multiturn",
        community_id="acme",
        turns=("I'm preparing the weekly update.", "How many members joined last week?"),
        expected_answer=1,
        expected_tools=(ToolCall("count_members_joined_last_week", {"community_id": "acme"}),),
        description="Multi-turn analytics request uses only the active tenant.",
    ),
    Scenario(
        id="add-member",
        community_id="acme",
        turns=("Add noah to the makers space.",),
        expected_answer={"member_id": "noah", "space_slug": "makers", "status": "added"},
        expected_tools=(ToolCall("add_member_to_space", {"community_id": "acme", "member_id": "noah", "space_slug": "makers"}),),
        description="Membership mutation is scoped to the requested community.",
    ),
    Scenario(
        id="create-event",
        community_id="acme",
        turns=("Create an event called Demo Day on 2026-11-10.",),
        expected_answer={"id": "evt_1", "title": "Demo Day", "starts_at": "2026-11-10"},
        expected_tools=(ToolCall("create_event", {"community_id": "acme", "title": "Demo Day", "starts_at": "2026-11-10"}),),
        description="Event creation produces a tenant-local event.",
    ),
)

# A dedicated adversarial test: request crosses tenants, but the tool receives acme's
# scope and must reject rival-only member / space references.
ISOLATION_SCENARIO = Scenario(
    id="cross-community-isolation",
    community_id="acme",
    turns=("Add riley to the private space.",),
    expected_answer=None,
    expected_tools=(ToolCall("add_member_to_space", {"community_id": "acme", "member_id": "riley", "space_slug": "private"}),),
    description="A malicious or confused request cannot read or mutate a different community.",
)
