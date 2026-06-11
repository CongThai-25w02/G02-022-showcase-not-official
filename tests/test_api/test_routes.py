from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.world import World, set_current_world

SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"


def _load_basic() -> None:
    set_current_world(World.from_scenario(SCENARIO_DIR / "warehouse_basic.json"))


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.asyncio
async def test_get_world(client):
    _load_basic()
    response = await client.get("/api/v1/world")
    assert response.status_code == 200
    data = response.json()
    assert data["robot"]["kind"] == "robot"
    assert data["width"] == 16


@pytest.mark.asyncio
async def test_load_scenario_basic(client):
    response = await client.post("/api/v1/scenario?name=warehouse_basic")
    assert response.status_code == 200
    assert response.json()["width"] == 16


@pytest.mark.asyncio
async def test_load_scenario_blocked(client):
    response = await client.post("/api/v1/scenario?name=warehouse_blocked")
    assert response.status_code == 200
    assert len(response.json()["people"]) == 1


@pytest.mark.asyncio
async def test_load_scenario_not_found(client):
    response = await client.post("/api/v1/scenario?name=does_not_exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_run_endpoint_returns_trace(client):
    """POST /run with mocked LLM returns plan + history + answer."""
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
            msg.content = json.dumps(["bước 1"])
        else:
            msg.content = ""
            msg.tool_calls = [{"name": "done", "args": {"summary": "xong"}, "id": "t1"}]
        return msg

    mock_llm = MagicMock()
    mock_llm.ainvoke = fake_ainvoke
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)

    with patch("src.agents.nodes.parse_goal.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.plan_node.get_llm", return_value=mock_llm), \
         patch("src.agents.nodes.act_node.get_llm", return_value=mock_llm):
        response = await client.post(
            "/api/v1/run",
            json={"goal_text": "Đưa pallet A tới chuyền 3"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert "history" in data
    assert "answer" in data
    assert "status" in data
    assert isinstance(data["history"], list)
    assert len(data["history"]) >= 1
