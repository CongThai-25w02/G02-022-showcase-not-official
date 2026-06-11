"""act node: LLM picks exactly ONE tool per step and executes it."""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import AgentState
from src.agents.tools.tools import ALL_TOOLS
from src.services.llm import get_llm

_SYSTEM = """Bạn là robot kho thực thi kế hoạch từng bước một.
Dựa trên kế hoạch còn lại và trạng thái hiện tại, gọi ĐÚNG MỘT tool phù hợp nhất cho bước này.
Observation là kết quả thật từ World sim — không được bịa.
Nếu đã đạt mục tiêu, gọi tool 'done' với tóm tắt.
Nếu gặp người chắn lối, gọi 'wait' hoặc 'ask_human'."""


async def act_node(state: AgentState) -> dict:
    goal = state.get("goal") or {}
    plan = state.get("plan") or []
    world_view = state.get("world_view") or {}
    history = list(state.get("history") or [])
    steps = state.get("steps") or 0

    context = (
        f"Mục tiêu: {json.dumps(goal, ensure_ascii=False)}\n"
        f"Kế hoạch còn lại: {json.dumps(plan, ensure_ascii=False)}\n"
        f"Trạng thái: {json.dumps(world_view, ensure_ascii=False)}\n"
        f"Lịch sử ({len(history)} bước): {json.dumps(history[-3:], ensure_ascii=False)}"
    )

    llm = get_llm().bind_tools(ALL_TOOLS)
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=context)]
    response = await llm.ainvoke(msgs)

    tool_map = {t.name: t for t in ALL_TOOLS}

    if response.tool_calls:
        # Execute only the FIRST tool call — 1 action = 1 step
        tc = response.tool_calls[0]
        t = tool_map.get(tc["name"])
        if t is None:
            obs = json.dumps({"error": f"unknown_tool: {tc['name']}"})
            ok = False
        else:
            try:
                obs = t.invoke(tc["args"])
                ok = True
            except Exception as exc:  # noqa: BLE001
                obs = json.dumps({"error": str(exc)})
                ok = False
        entry = {"action": tc["name"], "args": tc["args"], "observation": obs, "ok": ok}
    else:
        c = response.content
        obs_text = (" ".join(p.get("text","") if isinstance(p,dict) else str(p) for p in c) if isinstance(c,list) else str(c))
        entry = {"action": "llm_text", "args": {}, "observation": obs_text, "ok": False}

    history.append(entry)
    return {"history": history, "steps": steps + 1}
