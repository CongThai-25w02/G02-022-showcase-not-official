"""9 world-operation tools exposed to the LangGraph agent via Gemini function-calling.

Every tool reads/writes the *real* World singleton — no hallucination of results.
"""
from __future__ import annotations

import json

from langchain_core.tools import tool

from src.models.schemas import Cell
from src.services.world import get_current_world

# ---------------------------------------------------------------------------
# Perception tools (read-only)
# ---------------------------------------------------------------------------


@tool
def perceive() -> str:
    """Quan sát trạng thái thế giới xung quanh robot.

    Trả về: robot (pos, carrying), danh sách objects, people, obstacles, zones, tick.
    Gọi trước khi lập kế hoạch hoặc sau mỗi hành động để cập nhật world_view.
    """
    w = get_current_world()
    s = w.to_state()
    result = {
        "robot": {"pos": s.robot.pos.model_dump(), "carrying": s.robot.carrying},
        "objects": [
            {"id": o.id, "label": o.label, "pos": o.pos.model_dump()}
            for o in s.objects
            if o.pos.x >= 0
        ],
        "people": [
            {"id": p.id, "label": p.label, "pos": p.pos.model_dump()}
            for p in s.people
        ],
        "obstacles": [
            {"id": ob.id, "pos": ob.pos.model_dump()}
            for ob in s.obstacles
        ],
        "zones": [
            {
                "name": z.name,
                "cells": [c.model_dump() for c in z.cells],
            }
            for z in s.zones
        ],
        "tick": s.tick,
    }
    return json.dumps(result, ensure_ascii=False)


@tool
def locate_object(label: str) -> str:
    """Tìm vị trí của một vật thể theo nhãn (hỗ trợ khớp không phân biệt hoa/thường, dấu).

    Args:
        label: Nhãn vật cần tìm (vd "pallet A", "thùng B").

    Trả về: found, id, pos, zone (tên vùng nếu có), relative (trái/phải, gần/xa so với robot).
    """
    w = get_current_world()
    obj = w.find_object_fuzzy(label)
    if obj is None or obj.pos.x < 0:
        return json.dumps({"found": False})
    zone = w.cell_zone(obj.pos)
    rel = w.relative_position(obj.pos)
    return json.dumps(
        {
            "found": True,
            "id": obj.id,
            "pos": obj.pos.model_dump(),
            "zone": zone,
            "relative": rel,
        },
        ensure_ascii=False,
    )


@tool
def check_path(target_x: int, target_y: int) -> str:
    """Kiểm tra đường đi từ robot tới ô (target_x, target_y) có bị chặn không.

    Args:
        target_x: Tọa độ x của đích.
        target_y: Tọa độ y của đích.

    Trả về: clear (bool), blocker (entity bị chặn nếu có).
    """
    w = get_current_world()
    start = w.to_state().robot.pos
    goal = Cell(x=target_x, y=target_y)
    # Try path that avoids people
    path = w.astar(start, goal)
    if path is not None:
        return json.dumps({"clear": True})
    # No path with people — find first person blocking the static path
    static_path = w.astar_static(start, goal)
    if static_path is None:
        return json.dumps({"clear": False, "blocker": None, "reason": "no_path"})
    for cell in static_path[1:]:
        person = w.person_at(cell)
        if person is not None:
            return json.dumps({"clear": False, "blocker": person.model_dump()})
    return json.dumps({"clear": False, "blocker": None, "reason": "no_path"})


# ---------------------------------------------------------------------------
# Action tools (mutate world)
# ---------------------------------------------------------------------------


@tool
def move_to(target_x: int, target_y: int) -> str:
    """Di chuyển robot tới ô (target_x, target_y) theo đường A* (tránh obstacle tĩnh).

    Dừng ngay nếu ô kế có người — agent cần replan hoặc wait.

    Args:
        target_x: Tọa độ x đích.
        target_y: Tọa độ y đích.

    Trả về: reached (bool), pos hiện tại, blocked_by (entity người nếu bị chặn).
    """
    w = get_current_world()
    result = w.move_robot_to(Cell(x=target_x, y=target_y))
    return json.dumps(result, ensure_ascii=False)


@tool
def pick(object_id_or_label: str) -> str:
    """Nhặt vật thể gần robot (cùng ô hoặc kề).

    Args:
        object_id_or_label: ID hoặc nhãn vật thể (vd "pallet-A" hoặc "pallet A").

    Trả về: ok (bool), carrying (id), error (nếu thất bại).
    """
    w = get_current_world()
    result = w.pick_object(object_id_or_label)
    return json.dumps(result, ensure_ascii=False)


@tool
def drop(target_x: int, target_y: int) -> str:
    """Đặt vật đang mang xuống ô (target_x, target_y).

    Args:
        target_x: Tọa độ x nơi đặt.
        target_y: Tọa độ y nơi đặt.

    Trả về: ok (bool), dropped (id), at (pos), error (nếu thất bại).
    """
    w = get_current_world()
    result = w.drop_at(Cell(x=target_x, y=target_y))
    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Meta / safety tools
# ---------------------------------------------------------------------------


@tool
def wait(ticks: int = 1) -> str:
    """Chờ một số tick và quan sát lại (người có thể đã di chuyển).

    Args:
        ticks: Số tick chờ (mặc định 1).

    Trả về: tick mới + world_view cập nhật.
    """
    w = get_current_world()
    w.advance_tick(max(1, ticks))
    return perceive.invoke({})  # type: ignore[attr-defined]


@tool
def ask_human(question: str) -> str:
    """Dừng và hỏi vận hành viên khi bất định hoặc có người chắn lối.

    Args:
        question: Câu hỏi gửi tới người dùng.

    Trả về: paused=True, question. Agent phải dừng cho tới khi nhận được trả lời.
    """
    return json.dumps({"paused": True, "question": question}, ensure_ascii=False)


@tool
def done(summary: str) -> str:
    """Khai báo hoàn thành tác vụ và cung cấp tóm tắt.

    Args:
        summary: Tóm tắt kết quả (tiếng Việt).

    Trả về: done=True, summary.
    """
    return json.dumps({"done": True, "summary": summary}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Public list used by graph / bind_tools
# ---------------------------------------------------------------------------

ALL_TOOLS = [perceive, locate_object, check_path, move_to, pick, drop, wait, ask_human, done]
