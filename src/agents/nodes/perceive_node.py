"""perceive node: call perceive tool → update world_view in state."""
from __future__ import annotations

import json

from src.agents.state import AgentState
from src.agents.tools.tools import perceive


async def perceive_node(state: AgentState) -> dict:
    raw = perceive.invoke({})
    world_view = json.loads(raw)
    return {"world_view": world_view}
