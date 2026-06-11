from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph state for the task-planning agent."""

    goal_text: str
    goal: dict | None
    plan: list[str]
    history: list[dict]
    world_view: dict
    status: str
    replans: int
    steps: int
    answer: str
    pending_question: str | None
