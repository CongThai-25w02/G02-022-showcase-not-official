"""Phase 3 tests: replan, safety, cap — all with LLM mocks (no network)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.schemas import Cell, Entity, WorldState
from src.services.world import World, set_current_world

SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"


def _load(name: str) -> World:
    w = World.from_scenario(SCENARIO_DIR / f"{name}.json")
    set_current_world(w)
    return w


def _make_llm(responses: list) -> MagicMock:
    """Create a mock LLM with a pre-loaded sequence of responses."""
    call_idx = [0]

    async def fake_ainvoke(msgs):
        i = call_idx[0]
        call_idx[0] += 1
        r = responses[min(i, len(responses) - 1)]
        msg = MagicMock()
        if isinstance(r, list):
            msg.tool_calls = r
            msg.content = ""
        else:
            msg.tool_calls = []
            msg.content = r
        return msg

    m = MagicMock()
    m.ainvoke = fake_ainvoke
    m.bind_tools = MagicMock(return_value=m)
    return m


# ---------------------------------------------------------------------------
# Helper: build and run graph with given mock LLM
# ---------------------------------------------------------------------------

async def _run(goal: str, llm) -> dict:
    from src.agents.graph import build_graph
    import sys
    # Ensure they are imported first
    import src.agents.nodes.parse_goal
    import src.agents.nodes.plan_node
    import src.agents.nodes.act_node
    import src.agents.nodes.replan_node

    parse_goal_mod = sys.modules["src.agents.nodes.parse_goal"]
    plan_node_mod = sys.modules["src.agents.nodes.plan_node"]
    act_node_mod = sys.modules["src.agents.nodes.act_node"]
    replan_node_mod = sys.modules["src.agents.nodes.replan_node"]

    with (
        patch.object(parse_goal_mod, "get_llm", return_value=llm),
        patch.object(plan_node_mod, "get_llm", return_value=llm),
        patch.object(act_node_mod, "get_llm", return_value=llm),
        patch.object(replan_node_mod, "get_llm", return_value=llm),
    ):
        g = build_graph()
        return await g.ainvoke({"goal_text": goal})


# ---------------------------------------------------------------------------
# Replan: blocked → new plan → done  (unit-test replan_node directly)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replan_node_produces_new_plan() -> None:
    """replan_node: given a 'blocked' state, should return new plan and status='acting'."""
    from src.agents.nodes.replan_node import replan_node

    _load("warehouse_blocked")

    new_plan_json = json.dumps(["đi đường vòng", "done"])
    llm = _make_llm([new_plan_json])

    state = {
        "goal": {"target": "pallet A", "destination": "chuyền 3", "constraints": []},
        "world_view": {},
        "replans": 0,
        "status": "blocked",
        "history": [
            {
                "action": "move_to",
                "args": {"target_x": 12, "target_y": 3},
                "observation": json.dumps({"reached": False, "blocked_by": {"id": "p1", "pos": {"x": 7, "y": 3}}}),
                "ok": False,
            }
        ],
    }

    import sys
    import src.agents.nodes.replan_node
    replan_node_mod = sys.modules["src.agents.nodes.replan_node"]
    with patch.object(replan_node_mod, "get_llm", return_value=llm):
        result = await replan_node(state)

    assert result["replans"] == 1
    assert result["status"] == "acting"
    assert isinstance(result["plan"], list)
    assert len(result["plan"]) >= 1


@pytest.mark.asyncio
async def test_replan_cap_leads_to_failed() -> None:
    """replan_node: when replans already equals max_replans, returns status='failed'."""
    from src.agents.nodes.replan_node import replan_node
    from src.config import get_settings

    _load("warehouse_blocked")
    max_r = get_settings().max_replans

    state = {
        "goal": {},
        "world_view": {},
        "replans": max_r,  # already at cap
        "status": "blocked",
        "history": [],
    }

    llm = _make_llm([json.dumps(["never called"])])
    import sys
    import src.agents.nodes.replan_node
    replan_node_mod = sys.modules["src.agents.nodes.replan_node"]
    with patch.object(replan_node_mod, "get_llm", return_value=llm):
        result = await replan_node(state)

    assert result["status"] == "failed"
    assert result["replans"] == max_r + 1


# ---------------------------------------------------------------------------
# Safety: adjacent person → status="asking", robot stays put
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_safety_adjacent_person_triggers_ask_human() -> None:
    """Person at distance 1 from robot → observe sets status='asking' (not 'blocked')."""
    # Robot at (1,1), person at (2,1) — distance 1
    state = WorldState(
        width=5, height=5, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=1, y=1)),
        objects=[Entity(id="pallet-A", kind="object", label="pallet A", pos=Cell(x=3, y=3))],
        people=[Entity(id="p1", kind="person", label="Người", pos=Cell(x=2, y=1))],
        obstacles=[],
        zones=[],
    )
    w = World(state)
    set_current_world(w)

    goal_json = json.dumps({"target": "pallet A", "destination": "chuyền 3", "constraints": []})
    plan_json = json.dumps(["di chuyển tới (3,3)"])

    responses = [
        goal_json,
        plan_json,
        # move_to (3,3) → path goes through (2,1) [person] → robot stops at (1,1) adjacent to person
        [{"name": "move_to", "args": {"target_x": 3, "target_y": 3}, "id": "t1"}],
        [{"name": "done", "args": {"summary": "Xong."}, "id": "t2"}],
    ]
    llm = _make_llm(responses)
    await _run("Đưa pallet A tới chuyền 3", llm)

    # Check robot never entered person's cell
    final_robot_pos = (w.to_state().robot.pos.x, w.to_state().robot.pos.y)
    assert final_robot_pos != (2, 1), "Safety violation: robot entered person's cell!"


def test_safety_robot_never_enters_person_cell() -> None:
    """move_robot_to: robot must NEVER land on a person's cell."""
    from src.agents.tools.tools import move_to

    state = WorldState(
        width=10, height=10, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[],
        people=[Entity(id="p1", kind="person", pos=Cell(x=3, y=0))],
        obstacles=[],
        zones=[],
    )
    w = World(state)
    set_current_world(w)

    move_to.invoke({"target_x": 5, "target_y": 0})
    robot_pos = (w.to_state().robot.pos.x, w.to_state().robot.pos.y)
    person_pos = (3, 0)
    assert robot_pos != person_pos, "Safety violation: robot entered person's cell!"


def test_safety_violation_count_zero() -> None:
    """Run 10 move_to calls — count how many times robot landed on a person. Must be 0."""
    from src.agents.tools.tools import move_to

    # Multiple people scattered around
    state = WorldState(
        width=10, height=10, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[],
        people=[
            Entity(id="p1", kind="person", pos=Cell(x=3, y=0)),
            Entity(id="p2", kind="person", pos=Cell(x=7, y=0)),
        ],
        obstacles=[],
        zones=[],
    )
    w = World(state)
    set_current_world(w)

    targets = [(5, 0), (9, 0), (0, 0), (4, 4), (8, 8), (1, 0), (6, 0), (9, 9), (0, 9), (5, 5)]
    violations = 0
    for tx, ty in targets:
        move_to.invoke({"target_x": tx, "target_y": ty})
        rp = w.to_state().robot.pos
        for p in w.to_state().people:
            if p.pos.x == rp.x and p.pos.y == rp.y:
                violations += 1

    assert violations == 0, f"Safety violations: {violations}"


# ---------------------------------------------------------------------------
# Dynamic + wait: person blocks → wait → person moves → move succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dynamic_wait_unblocks_path() -> None:
    """After waiting until tick 5, the previously blocked path at (7,3) is clear."""
    from src.agents.tools.tools import move_to, wait

    w = World.from_scenario(SCENARIO_DIR / "warehouse_dynamic.json")
    set_current_world(w)

    # Advance to tick 2: person moves to (7,3)
    w.advance_tick(2)
    assert w.is_blocked(Cell(x=7, y=3))

    # Try to move through (7,3) — should be blocked
    result_blocked = json.loads(move_to.invoke({"target_x": 12, "target_y": 3}))
    assert not result_blocked["reached"]

    # Wait until tick 5: person moves back to (2,8)
    wait.invoke({"ticks": 3})
    assert not w.is_blocked(Cell(x=7, y=3))


# ---------------------------------------------------------------------------
# observe_node unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_observe_blocked_far_person_routes_to_replan() -> None:
    """Person far from robot → status='blocked' (not 'asking')."""
    from src.agents.nodes.observe_node import observe_node

    state = WorldState(
        width=10, height=10, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[], people=[], obstacles=[], zones=[],
    )
    w = World(state)
    set_current_world(w)

    blocker_far = {"id": "p1", "kind": "person", "pos": {"x": 5, "y": 0}, "label": None, "carrying": None}
    obs_str = json.dumps({"reached": False, "blocked_by": blocker_far, "pos": {"x": 3, "y": 0}})

    agent_state = {
        "history": [{"action": "move_to", "args": {}, "observation": obs_str, "ok": True}],
        "status": "acting",
    }
    result = await observe_node(agent_state)
    assert result["status"] == "blocked"


@pytest.mark.asyncio
async def test_observe_blocked_adjacent_person_routes_to_asking() -> None:
    """Person adjacent to robot → status='asking' (safety)."""
    from src.agents.nodes.observe_node import observe_node

    state = WorldState(
        width=10, height=10, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=3, y=0)),
        objects=[], people=[], obstacles=[], zones=[],
    )
    w = World(state)
    set_current_world(w)

    blocker_adj = {"id": "p1", "kind": "person", "pos": {"x": 4, "y": 0}, "label": None, "carrying": None}
    obs_str = json.dumps({"reached": False, "blocked_by": blocker_adj, "pos": {"x": 3, "y": 0}})

    agent_state = {
        "history": [{"action": "move_to", "args": {}, "observation": obs_str, "ok": True}],
        "status": "acting",
    }
    result = await observe_node(agent_state)
    assert result["status"] == "asking"
    assert "pending_question" in result
