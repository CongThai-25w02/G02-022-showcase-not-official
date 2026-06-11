"""summarize node: produce final answer + compact trace."""
from __future__ import annotations

from src.agents.state import AgentState


async def summarize_node(state: AgentState) -> dict:
    status = state.get("status", "done")
    existing_answer = state.get("answer", "")
    history = state.get("history") or []
    replans = state.get("replans") or 0

    if existing_answer:
        return {"answer": existing_answer, "status": status}

    steps_done = len([h for h in history if h.get("ok")])
    total = len(history)

    if status == "failed":
        answer = (
            f"Tác vụ thất bại sau {total} bước ({steps_done} thành công)"
            + (f", {replans} lần replan." if replans else ".")
        )
    elif status == "asking":
        question = state.get("pending_question") or ""
        answer = f"Tạm dừng — cần xác nhận: {question}"
    else:
        answer = f"Hoàn thành. {steps_done}/{total} bước thành công."

    return {"answer": answer, "status": status}
