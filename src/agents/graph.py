from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.nodes import (
    act_node,
    observe_node,
    parse_goal_node,
    perceive_node,
    plan_node,
    replan_node,
    summarize_node,
)
from src.agents.routing import decide_observe_route
from src.agents.state import AgentState
from src.config import get_settings

# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------


def _route_observe(state: AgentState) -> str:
    settings = get_settings()
    return decide_observe_route(
        state.get("status", "acting"),
        state.get("steps") or 0,
        settings.max_steps,
        settings.core_scope,
    )


def _route_replan(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "summarize"
    return "act"


async def _cap_node(state: AgentState) -> dict:
    """Marks status=failed when step cap is exceeded, then feeds into summarize."""
    steps = state.get("steps") or 0
    return {"status": "failed", "answer": f"Vượt giới hạn {steps} bước — tác vụ bị dừng."}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("parse_goal", parse_goal_node)
    g.add_node("perceive", perceive_node)
    g.add_node("plan", plan_node)
    g.add_node("act", act_node)
    g.add_node("observe", observe_node)
    g.add_node("replan", replan_node)
    g.add_node("cap", _cap_node)
    g.add_node("summarize", summarize_node)

    # Linear entry sequence
    g.set_entry_point("parse_goal")
    g.add_edge("parse_goal", "perceive")
    g.add_edge("perceive", "plan")
    g.add_edge("plan", "act")
    g.add_edge("act", "observe")

    # observe → act (loop) | replan | summarize | cap
    g.add_conditional_edges(
        "observe",
        _route_observe,
        {
            "act": "act",
            "replan": "replan",
            "summarize": "summarize",
            "cap_exceeded": "cap",
        },
    )

    # replan → act (new plan) | summarize (max replans hit)
    g.add_conditional_edges(
        "replan",
        _route_replan,
        {
            "act": "act",
            "summarize": "summarize",
        },
    )

    g.add_edge("cap", "summarize")
    g.add_edge("summarize", END)
    return g.compile()


agent = build_graph()
