from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .models import ToolCall


class CommunityStore:
    """In-memory, tenant-scoped fake Circle data. Every tool requires community_id."""

    def __init__(self) -> None:
        self.communities: dict[str, dict[str, Any]] = {
            "acme": {
                "spaces": {"makers": {"members": {"maya"}}},
                "members": {"maya": {"joined": "2026-10-20"}, "noah": {"joined": "2026-10-29"}},
                "events": [],
            },
            "rival": {
                "spaces": {"private": {"members": {"riley", "robin"}}},
                "members": {"riley": {"joined": "2026-10-30"}, "robin": {"joined": "2026-10-10"}},
                "events": [],
            },
        }

    def _community(self, community_id: str) -> dict[str, Any]:
        if community_id not in self.communities:
            raise ValueError("unknown community")
        return self.communities[community_id]

    def create_event(self, community_id: str, title: str, starts_at: str) -> dict[str, str]:
        community = self._community(community_id)
        event = {"id": f"evt_{len(community['events']) + 1}", "title": title, "starts_at": starts_at}
        community["events"].append(event)
        return event

    def add_member_to_space(self, community_id: str, member_id: str, space_slug: str) -> dict[str, str]:
        community = self._community(community_id)
        if member_id not in community["members"]:
            raise ValueError("member does not belong to this community")
        if space_slug not in community["spaces"]:
            raise ValueError("space does not belong to this community")
        community["spaces"][space_slug]["members"].add(member_id)
        return {"member_id": member_id, "space_slug": space_slug, "status": "added"}

    def count_members_joined_last_week(self, community_id: str, today: date = date(2026, 11, 2)) -> int:
        community = self._community(community_id)
        # Previous calendar week: Mon Oct 26 through Sun Nov 1 for the fixed demo date.
        this_monday = today - timedelta(days=today.weekday())
        start, end = this_monday - timedelta(days=7), this_monday
        return sum(start <= date.fromisoformat(member["joined"]) < end for member in community["members"].values())

    def execute(self, call: ToolCall) -> Any:
        methods = {
            "create_event": self.create_event,
            "add_member_to_space": self.add_member_to_space,
            "count_members_joined_last_week": self.count_members_joined_last_week,
        }
        if call.name not in methods:
            raise ValueError(f"unsupported tool: {call.name}")
        return methods[call.name](**call.arguments)
