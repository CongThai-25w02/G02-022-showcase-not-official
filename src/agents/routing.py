"""Routing thuần cho agent graph — tách khỏi LangGraph để test được, không deps nặng.

`decide_observe_route()` là logic rẽ nhánh sau node `observe`. Tách ra đây để
unit-test trực tiếp (PLAN_thu_nho_162.md). `core_scope=True` = scope v2 'di chuyển
1 vật thể': khi bị chặn thì KẾT THÚC thay vì replan (bỏ nhánh replan/ask_human).
"""
from __future__ import annotations


def decide_observe_route(
    status: str, steps: int, max_steps: int, core_scope: bool = False
) -> str:
    """Node kế tiếp sau `observe`: act | replan | summarize | cap_exceeded."""
    if steps >= max_steps:
        return "cap_exceeded"
    if status in ("done", "asking"):
        return "summarize"
    if status == "blocked":
        return "summarize" if core_scope else "replan"
    return "act"
