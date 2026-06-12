"""Scenario metadata for the web UI (dropdown + quick eval chips)."""

from __future__ import annotations

import json
from pathlib import Path

_SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"

GROUPS: list[tuple[str, str]] = [
    ("demo", "Demo kho (live)"),
    ("eval_v2", "Eval v2 — metrics (m01–m11)"),
    ("eval_v1", "Eval v1 — bộ task (t01–t19)"),
]

# Vietnamese labels for UI (key = filename without .json)
LABELS: dict[str, str] = {
    "warehouse_blocked": "Kho có người chặn lối (hero)",
    "warehouse_basic": "Kho cơ bản (không người)",
    "warehouse_dynamic": "Kho động (người di chuyển)",
    "m01_basic_a": "m01 — Di chuyển pallet A → chuyền 3",
    "m02_basic_b": "m02 — Đưa thùng B → kho B",
    "m03_basic_c": "m03 — Mang kiện C → chuyền 3",
    "m04_obstacle_wall": "m04 — Vượt tường cản tĩnh",
    "m05_obstacle_detour": "m05 — Đi vòng chướng ngại",
    "m06_obstacle_narrow": "m06 — Hành lang hẹp",
    "m07_pickdrop_far": "m07 — Gắp thả khoảng cách xa",
    "m08_pickdrop_cross": "m08 — Gắp thả chéo kho",
    "m09_language_case": "m09 — Kiểm tra chữ hoa/thường",
    "m10_infeasible_missing": "m10 — Pallet không tồn tại",
    "m11_infeasible_enclosed": "m11 — Hàng bị bịt kín",
    "t01_basic_move": "t01 — Di chuyển cơ bản",
    "t02_basic_drop": "t02 — Đưa thùng B → khu A",
    "t03_obstacle_route": "t03 — Đi vòng qua tường",
    "t04_obstacle_narrow": "t04 — Hành lang hẹp một lối",
    "t05_pick_move_first": "t05 — Phải đến gần mới gắp",
    "t06_multi_goal": "t06 — Đa mục tiêu (A rồi B)",
    "t07_language_case": "t07 — Chữ hoa/thường pallet",
    "t08_language_constraint": "t08 — Ràng buộc tránh người",
    "t09_replan_person_blocks": "t09 — Người chặn giữa chừng",
    "t10_replan_detour": "t10 — Replan đường vòng dài",
    "t11_replan_wait": "t11 — Chờ người rồi đi",
    "t12_safety_adjacent": "t12 — Người sát robot → dừng",
    "t13_safety_at_dest": "t13 — Người chắn ngay đích",
    "t14_safety_two_people": "t14 — Hai người cắt đường",
    "t15_infeasible_enclosed": "t15 — Đích bị bao kín",
    "t16_infeasible_missing": "t16 — Vật không tồn tại",
    "t17_robustness_vague": "t17 — Mệnh lệnh mơ hồ",
    "t18_robustness_large": "t18 — Bản đồ lớn nhiều nhiễu",
    "t19_replan_midpath_block": "t19 — Replan giữa đường",
}

DEFAULT_GOALS: dict[str, str] = {
    "warehouse_blocked": "Đưa pallet A tới chuyền 3, tránh người",
    "warehouse_basic": "Đưa pallet A tới chuyền 3",
    "warehouse_dynamic": "Đưa pallet A tới chuyền 3",
}

# One representative scenario per eval category for quick-launch chips
EVAL_QUICK: list[dict[str, str]] = [
    {"id": "m01_basic_a", "icon": "📦", "text": "Basic", "cap": "di chuyển cơ bản"},
    {"id": "m04_obstacle_wall", "icon": "🧱", "text": "Vật cản", "cap": "A* đi vòng tường"},
    {"id": "m07_pickdrop_far", "icon": "🔄", "text": "Gắp/thả", "cap": "pick xa → drop"},
    {"id": "m09_language_case", "icon": "🔤", "text": "Ngôn ngữ", "cap": "chữ hoa/thường"},
    {"id": "t10_replan_detour", "icon": "🚧", "text": "Replan", "cap": "đổi đường vòng"},
    {"id": "t13_safety_at_dest", "icon": "🛑", "text": "An toàn", "cap": "người chắn đích"},
    {"id": "m10_infeasible_missing", "icon": "⛔", "text": "Bất khả thi", "cap": "hàng không có"},
    {"id": "t17_robustness_vague", "icon": "❓", "text": "Mơ hồ", "cap": "agent hỏi lại"},
]


def _scenario_group(name: str) -> str:
    if name.startswith("warehouse_"):
        return "demo"
    if name.startswith("m"):
        return "eval_v2"
    if name.startswith("t"):
        return "eval_v1"
    return "demo"


def _group_label(group_id: str) -> str:
    for gid, label in GROUPS:
        if gid == group_id:
            return label
    return group_id


def list_scenarios() -> list[dict]:
    """Return sorted scenario metadata for the frontend."""
    items: list[dict] = []
    for path in sorted(_SCENARIO_DIR.glob("*.json")):
        if path.name == "SPEC.md":
            continue
        name = path.stem
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        task = data.get("task") or {}
        items.append(
            {
                "id": name,
                "label": LABELS.get(name, name.replace("_", " ")),
                "group": _scenario_group(name),
                "group_label": _group_label(_scenario_group(name)),
                "category": task.get("category"),
                "goal_text": task.get("goal_text") or DEFAULT_GOALS.get(name, ""),
                "feasible": task.get("feasible"),
            }
        )

    group_order = {gid: i for i, (gid, _) in enumerate(GROUPS)}
    items.sort(key=lambda s: (group_order.get(s["group"], 99), s["id"]))
    return items
