"""Test routing thuần (PLAN_thu_nho_162.md) — không cần LangGraph."""
from __future__ import annotations

from src.agents.routing import decide_observe_route


def test_cap_exceeded_takes_priority() -> None:
    assert decide_observe_route("blocked", 40, 40) == "cap_exceeded"
    assert decide_observe_route("acting", 41, 40) == "cap_exceeded"


def test_done_and_asking_go_summarize() -> None:
    assert decide_observe_route("done", 0, 40) == "summarize"
    assert decide_observe_route("asking", 0, 40) == "summarize"


def test_blocked_replans_by_default() -> None:
    assert decide_observe_route("blocked", 0, 40) == "replan"


def test_blocked_summarizes_in_core_scope() -> None:
    assert decide_observe_route("blocked", 0, 40, core_scope=True) == "summarize"


def test_acting_continues() -> None:
    assert decide_observe_route("acting", 0, 40) == "act"
    assert decide_observe_route("acting", 0, 40, core_scope=True) == "act"
