from __future__ import annotations

import re
from dataclasses import dataclass
from time import perf_counter

from .models import ToolCall, Turn
from .store import CommunityStore


@dataclass
class CommunityAdminAgent:
    """A deliberately small, inspectable agent used to validate the eval harness.

    Replace `plan` with an LLM adapter for production experiments; the tool boundary
    and evaluators stay the same.
    """
    store: CommunityStore

    def plan(self, message: str, community_id: str) -> list[ToolCall]:
        lower = message.lower()
        if "how many" in lower and "joined last week" in lower:
            return [ToolCall("count_members_joined_last_week", {"community_id": community_id})]
        if "add" in lower and "space" in lower:
            match = re.search(r"add\s+([\w-]+).*?(?:to|in)\s+(?:the\s+)?([\w-]+)\s+space", lower)
            if not match:
                return []
            return [ToolCall("add_member_to_space", {"community_id": community_id, "member_id": match.group(1), "space_slug": match.group(2)})]
        if "event" in lower:
            title = re.search(r"(?:called|titled)\s+[\"']?(.+?)[\"']?(?:\s+on|$)", message, re.I)
            starts = re.search(r"\bon\s+(\d{4}-\d{2}-\d{2})", message)
            if title and starts:
                return [ToolCall("create_event", {"community_id": community_id, "title": title.group(1).strip(), "starts_at": starts.group(1)})]
        return []

    def respond(self, message: str, community_id: str) -> Turn:
        started = perf_counter()
        planned = self.plan(message, community_id)
        executed: list[ToolCall] = []
        result = None
        try:
            for call in planned:
                result = self.store.execute(call)
                executed.append(call)
            if planned and planned[0].name == "count_members_joined_last_week":
                answer = f"{result} members joined last week."
            elif planned:
                answer = "Done."
            else:
                answer = "I couldn't map that request to an available admin tool."
        except ValueError as error:
            answer = f"I can't do that: {error}."
        return Turn(user=message, assistant=answer, plan=planned, executed=executed, answer=result, latency_ms=(perf_counter() - started) * 1000)
