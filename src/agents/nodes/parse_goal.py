"""parse_goal node: natural-language Vietnamese goal → structured {target, destination, constraints}."""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.services.llm import get_llm

_SYSTEM = """Bạn là parser mục tiêu cho robot kho. Nhận mục tiêu tiếng Việt, trả về JSON:
{"target": "<vật cần di chuyển>", "destination": "<đích đến>", "constraints": ["<ràng buộc1>", ...]}
Chỉ trả JSON, không giải thích thêm."""


async def parse_goal_node(state: AgentState) -> dict:
    goal_text = state.get("goal_text", "")
    llm = get_llm()
    msgs = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=goal_text),
    ]
    response = await llm.ainvoke(msgs)
    # content may be str (OpenAI-style) or list of parts (Gemini multimodal)
    content = response.content
    if isinstance(content, list):
        raw = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content).strip()
    else:
        raw = str(content).strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        goal = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        goal = {"target": goal_text, "destination": "", "constraints": []}
    return {"goal": goal, "status": "planning", "replans": 0, "steps": 0, "history": [], "plan": []}
