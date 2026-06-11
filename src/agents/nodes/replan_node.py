"""replan node: LLM devises a new plan when the previous path was blocked."""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.config import get_settings
from src.services.llm import get_llm

_SYSTEM = """Bạn là planner cho robot kho. Đường đi bị chặn bởi người/vật cản.
Dựa trên thông tin chặn và trạng thái hiện tại, hãy lập kế hoạch MỚI để đạt mục tiêu:
- Đi đường vòng (nếu có), HOẶC
- Chờ (wait) rồi thử lại, HOẶC
- Gọi ask_human nếu lối bị chặn hoàn toàn.
Trả về JSON array các bước, tối đa 10 bước. Chỉ trả JSON array."""


async def replan_node(state: AgentState) -> dict:
    replans = (state.get("replans") or 0) + 1
    max_replans = get_settings().max_replans

    if replans > max_replans:
        return {
            "replans": replans,
            "status": "failed",
            "answer": f"Đã replan {replans - 1} lần, vẫn không tìm được đường đi.",
        }

    # Extract blocked_by from last history entry
    history = state.get("history") or []
    blocked_by: dict | None = None
    if history:
        last = history[-1]
        try:
            obs = json.loads(last.get("observation", "{}"))
            blocked_by = obs.get("blocked_by")
        except (json.JSONDecodeError, ValueError):
            pass

    goal = state.get("goal") or {}
    world_view = state.get("world_view") or {}

    prompt = (
        f"Mục tiêu: {json.dumps(goal, ensure_ascii=False)}\n"
        f"Chặn bởi: {json.dumps(blocked_by, ensure_ascii=False)}\n"
        f"Trạng thái thế giới: {json.dumps(world_view, ensure_ascii=False)}\n"
        f"Lần replan thứ {replans}/{max_replans}. Lập kế hoạch mới."
    )

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
        new_plan: list[str] = json.loads(raw)
        if not isinstance(new_plan, list):
            new_plan = [str(new_plan)]
    except (json.JSONDecodeError, ValueError):
        new_plan = [raw]

    return {"replans": replans, "plan": new_plan, "status": "acting"}
