"""observe node: examine last history entry, refresh world_view, decide next edge.

Safety invariant: if a person is within Manhattan distance ≤1 of the robot
after a blocked move, route to 'asking' (ask_human / wait) rather than 'replan',
so the robot never acts toward a person without human confirmation.
"""
from __future__ import annotations

import json

from src.agents.state import AgentState
from src.agents.tools.tools import perceive
from src.services.world import get_current_world


def _adjacent_to_robot(blocker_pos: dict, start_pos: dict | None = None) -> bool:
    """Return True if the person was adjacent at the START of the move_to call.

    Uses start_pos (robot pos before any steps) when available — this correctly
    identifies cases where the robot couldn't move at all (person was 1 cell away
    when the move began) vs cases where the robot moved several cells before
    encountering the person (person was blocking a mid-path segment → replan).
    """
    ref = start_pos if start_pos else get_current_world().to_state().robot.pos.model_dump()
    dist = abs(blocker_pos["x"] - ref["x"]) + abs(blocker_pos["y"] - ref["y"])
    return dist <= 1


async def observe_node(state: AgentState) -> dict:
    history = state.get("history") or []
    updates: dict = {}

    # Always refresh world_view after an action
    raw = perceive.invoke({})
    updates["world_view"] = json.loads(raw)

    if not history:
        updates["status"] = "acting"
        return updates

    last = history[-1]
    action = last.get("action", "")
    obs_raw = last.get("observation", "{}")

    try:
        obs = json.loads(obs_raw) if isinstance(obs_raw, str) else obs_raw
    except (json.JSONDecodeError, ValueError):
        obs = {}

    # ── Terminal: done — only accept if goal is actually achieved ─────────
    if action == "done" and obs.get("done"):
        goal = state.get("goal") or {}
        target = goal.get("target")
        destination = goal.get("destination")
        if target and destination:
            w = get_current_world()
            obj = w.find_object_fuzzy(target)
            zone_cells = w.zone_cells(destination)
            # Reject if: still carrying (pos.x < 0), object missing, or not in dest zone
            goal_met = (
                obj is not None
                and obj.pos.x >= 0
                and zone_cells
                and any(c.x == obj.pos.x and c.y == obj.pos.y for c in zone_cells)
            )
            if not goal_met:
                # Agent declared done prematurely — keep acting
                updates["status"] = "acting"
                return updates
        updates["status"] = "done"
        updates["answer"] = obs.get("summary", "Hoàn thành.")
        return updates

    # ── Terminal: ask_human (safety, human-in-loop) ───────────────────────
    if action == "ask_human" and obs.get("paused"):
        updates["status"] = "asking"
        updates["pending_question"] = obs.get("question")
        return updates

    # ── Blocked move ──────────────────────────────────────────────────────
    if action == "move_to" and not obs.get("reached", True) and "blocked_by" in obs:
        blocker = obs["blocked_by"] or {}
        blocker_pos = blocker.get("pos") or {}
        start_pos = obs.get("start_pos")

        # Safety: person was adjacent at move start → must wait/ask, not blindly replan
        if blocker_pos and _adjacent_to_robot(blocker_pos, start_pos):
            updates["status"] = "asking"
            updates["pending_question"] = (
                f"Người '{blocker.get('label', blocker.get('id', '?'))}' "
                f"đứng kề robot tại {blocker_pos}. Có thể tiếp tục không?"
            )
            return updates

        # Person is further away → replan to find alternate route
        updates["status"] = "blocked"
        return updates

    updates["status"] = "acting"
    return updates
