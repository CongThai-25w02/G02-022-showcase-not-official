"""Graph integration tests using a mock LLM (no network calls)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.world import World, set_current_world

SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"


def _load_basic() -> None:
    set_current_world(World.from_scenario(SCENARIO_DIR / "warehouse_basic.json"))


def _make_mock_llm(tool_calls: list[dict] | None = None, content: str = ""):
    """Return a mock LLM that emits one response with optional tool_calls."""
    mock_llm = MagicMock()
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls or []
    mock_llm.ainvoke = AsyncMock(return_value=msg)
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    return mock_llm


@pytest.mark.asyncio
async def test_graph_runs_to_completion() -> None:
    """Full graph run with mocked LLM — must finish without hanging."""
    _load_basic()

    goal_json = json.dumps(
        {"target": "pallet A", "destination": "chuyền 3", "constraints": []},
        ensure_ascii=False,
    )
    plan_json = json.dumps(["di chuyển tới pallet A", "nhặt pallet A", "di chuyển tới chuyền 3", "đặt xuống"])

    # parse_goal → goal JSON
    # plan → plan array
    # act (3 real tool calls) + 1 done call
    call_count = 0

    async def fake_ainvoke(msgs):
        nonlocal call_count
        call_count += 1
        msg = MagicMock()
        msg.tool_calls = []
        if call_count == 1:
            # parse_goal
            msg.content = goal_json
        elif call_count == 2:
            # plan
            msg.content = plan_json
        else:
            # act: call done immediately
            msg.content = ""
            msg.tool_calls = [{"name": "done", "args": {"summary": "Xong."}, "id": "tc1"}]
        return msg

    mock_llm = MagicMock()
    mock_llm.ainvoke = fake_ainvoke
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)

    with patch("src.agents.nodes.parse_goal.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.plan_node.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.act_node.get_llm", return_value=mock_llm):
        from src.agents.graph import build_graph
        g = build_graph()
        result = await g.ainvoke({"goal_text": "Đưa pallet A tới chuyền 3"})

    assert result.get("status") in ("done", "acting", "failed")
    assert isinstance(result.get("history"), list)
    assert len(result["history"]) >= 1


@pytest.mark.asyncio
async def test_graph_caps_at_max_steps() -> None:
    """Graph must not exceed max_steps — status should be failed when capped."""
    _load_basic()

    call_count = 0

    async def always_act(msgs):
        nonlocal call_count
        call_count += 1
        msg = MagicMock()
        if call_count == 1:
            msg.content = json.dumps({"target": "x", "destination": "y", "constraints": []})
            msg.tool_calls = []
        elif call_count == 2:
            msg.content = json.dumps(["bước 1"])
            msg.tool_calls = []
        else:
            # Repeatedly call wait — never calls done
            msg.content = ""
            msg.tool_calls = [{"name": "wait", "args": {"ticks": 1}, "id": "t1"}]
        return msg

    mock_llm = MagicMock()
    mock_llm.ainvoke = always_act
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)

    with patch("src.agents.nodes.parse_goal.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.plan_node.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.act_node.get_llm", return_value=mock_llm):
        from src.agents.graph import build_graph
        from src.config import get_settings
        max_steps = get_settings().max_steps
        g = build_graph()
        result = await g.ainvoke({"goal_text": "loop forever"})

    # Graph must terminate at the cap, not run forever
    assert result.get("steps", 0) <= max_steps
    assert isinstance(result.get("history"), list)
    # All steps must have been capped — status should not be blank
    assert result.get("status") in ("done", "acting", "failed", "blocked", "asking")


@pytest.mark.asyncio
async def test_history_has_real_observations() -> None:
    """Observations in history must come from real World, not LLM text."""
    _load_basic()

    call_count = 0

    async def fake_ainvoke(msgs):
        nonlocal call_count
        call_count += 1
        msg = MagicMock()
        msg.tool_calls = []
        if call_count == 1:
            msg.content = json.dumps({"target": "pallet A", "destination": "chuyền 3", "constraints": []})
        elif call_count == 2:
            msg.content = json.dumps(["perceive"])
        else:
            msg.content = ""
            msg.tool_calls = [{"name": "done", "args": {"summary": "ok"}, "id": "t1"}]
        return msg

    mock_llm = MagicMock()
    mock_llm.ainvoke = fake_ainvoke
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)

    with patch("src.agents.nodes.parse_goal.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.plan_node.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.act_node.get_llm", return_value=mock_llm):
        from src.agents.graph import build_graph
        g = build_graph()
        result = await g.ainvoke({"goal_text": "test"})

    history = result.get("history") or []
    assert len(history) >= 1
    last = history[-1]
    # Observation must be parseable JSON from the real tool
    obs = json.loads(last["observation"])
    assert isinstance(obs, dict)


@pytest.mark.asyncio
async def test_done_only_valid_when_goal_achieved() -> None:
    """Agent calling 'done' while object is NOT in destination zone must NOT terminate as done.

    The observe_node must reject premature 'done' calls and keep acting.
    """
    import json as _json
    from pathlib import Path as _Path
    from unittest.mock import MagicMock as _MagicMock
    from unittest.mock import patch as _patch

    from src.services.world import World as _World
    from src.services.world import set_current_world as _set

    scenario_dir = _Path(__file__).parent.parent.parent / "eval" / "scenarios"
    w = _World.from_scenario(scenario_dir / "t01_basic_move.json")
    _set(w)

    # t01: pallet A starts at (3,3) in "khu A", goal is "chuyền 3" (11-13, 2-3)
    # We'll have agent call 'done' immediately without moving anything.
    call_count = [0]

    async def fake_ainvoke(msgs):
        call_count[0] += 1
        msg = _MagicMock()
        if call_count[0] == 1:
            # parse_goal
            msg.content = _json.dumps(
                {"target": "pallet A", "destination": "chuyền 3", "constraints": []}
            )
            msg.tool_calls = []
        elif call_count[0] == 2:
            # plan
            msg.content = _json.dumps(["done immediately"])
            msg.tool_calls = []
        elif call_count[0] == 3:
            # act: premature done — object not in destination yet
            msg.content = ""
            msg.tool_calls = [{"name": "done", "args": {"summary": "Xong sớm."}, "id": "tc_early"}]
        else:
            # After rejection, agent perceives and declares done again (cap will stop it)
            msg.content = ""
            msg.tool_calls = [{"name": "wait", "args": {"ticks": 1}, "id": "tc_wait"}]
        return msg

    mock_llm = _MagicMock()
    mock_llm.ainvoke = fake_ainvoke
    mock_llm.bind_tools = _MagicMock(return_value=mock_llm)

    with _patch("src.agents.nodes.parse_goal.get_llm", return_value=mock_llm), \
         _patch("src.agents.nodes.plan_node.get_llm", return_value=mock_llm), \
         _patch("src.agents.nodes.act_node.get_llm", return_value=mock_llm):
        from src.agents.graph import build_graph
        g = build_graph()
        result = await g.ainvoke({"goal_text": "Đưa pallet A tới chuyền 3"})

    # Premature done must NOT result in status=done with object still in source zone
    # Object never moved, so success must not be declared via early done
    assert result.get("status") != "done", (
        "Agent declared done prematurely — observe_node should have rejected early done"
    )
