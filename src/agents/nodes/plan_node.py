"""plan node: LLM generates a list of action steps given goal + world_view."""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.services.llm import get_llm

_SYSTEM = """Bạn là planner cho robot kho 2D. Dựa trên mục tiêu và trạng thái thế giới, sinh kế hoạch dạng danh sách bước ngắn gọn (JSON array of strings).
Mỗi bước là lời mô tả hành động (vd "di chuyển tới (3,3)", "nhặt pallet A", "di chuyển tới chuyền 3", "đặt xuống").
Chỉ trả JSON array, không giải thích thêm. Tối đa 10 bước."""


async def plan_node(state: AgentState) -> dict:
    goal = state.get("goal") or {}
    world_view = state.get("world_view") or {}
    prompt = f"Mục tiêu: {json.dumps(goal, ensure_ascii=False)}\nThế giới: {json.dumps(world_view, ensure_ascii=False)}"

    llm = get_llm()
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]
    response = await llm.ainvoke(msgs)
    c = response.content
    raw = (" ".join(p.get("text","") if isinstance(p,dict) else str(p) for p in c) if isinstance(c,list) else str(c)).strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        plan: list[str] = json.loads(raw)
        if not isinstance(plan, list):
            plan = [str(plan)]
    except (json.JSONDecodeError, ValueError):
        plan = [raw]
    return {"plan": plan, "status": "acting"}
