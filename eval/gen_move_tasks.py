"""Sinh bộ task 'di chuyển 1 vật thể' (v2) — PLAN_thu_nho_162.md.

Mỗi task = WorldState 16x10 + khối `task` {goal_text, category, feasible, success}.
success = {object, at_zone} → chấm bằng oracle check_object_moved.
Chạy: python eval/gen_move_tasks.py  (ghi eval/scenarios/m*.json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.models.schemas import Cell, Entity, WorldState  # noqa: E402
from src.services.invariants import assert_invariants  # noqa: E402
from src.services.world import World  # noqa: E402

W, H = 16, 10
SCEN_DIR = Path(__file__).resolve().parent / "scenarios"

ZONES = [
    {"name": "khu A", "cells": [(2, 2), (3, 2), (2, 3), (3, 3)]},
    {"name": "chuyền 3", "cells": [(12, 2), (13, 2), (12, 3), (13, 3)]},
    {"name": "kho B", "cells": [(13, 7), (14, 7), (13, 8), (14, 8)]},
]

# id, goal, category, feasible, [(obj_id,label,x,y)], [(obs_x,obs_y)], {object,at_zone}
TASKS = [
    ("m01_basic_a", "Đưa pallet A từ khu A sang chuyền 3", "basic", True,
     [("pallet-A", "pallet A", 3, 3)], [], {"object": "pallet A", "at_zone": "chuyền 3"}),
    ("m02_basic_b", "Đưa thùng B tới kho B", "basic", True,
     [("box-B", "thùng B", 4, 6)], [], {"object": "thùng B", "at_zone": "kho B"}),
    ("m03_basic_c", "Mang kiện C tới chuyền 3", "basic", True,
     [("crate-C", "kiện C", 2, 7)], [], {"object": "kiện C", "at_zone": "chuyền 3"}),
    ("m04_obstacle_wall", "Đưa pallet A qua tường tới chuyền 3", "obstacle", True,
     [("pallet-A", "pallet A", 3, 4)],
     [(7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7)],
     {"object": "pallet A", "at_zone": "chuyền 3"}),
    ("m05_obstacle_detour", "Đưa thùng B vòng chướng ngại tới kho B", "obstacle", True,
     [("box-B", "thùng B", 5, 8)],
     [(9, 6), (9, 7), (9, 8), (9, 9)],
     {"object": "thùng B", "at_zone": "kho B"}),
    ("m06_obstacle_narrow", "Đưa kiện C qua lối hẹp tới chuyền 3", "obstacle", True,
     [("crate-C", "kiện C", 2, 5)],
     [(7, 0), (7, 1), (7, 2), (7, 4), (7, 5), (7, 6), (7, 7), (7, 8), (7, 9)],
     {"object": "kiện C", "at_zone": "chuyền 3"}),
    ("m07_pickdrop_far", "Nhặt pallet A và đưa tới chuyền 3", "pick/drop", True,
     [("pallet-A", "pallet A", 8, 8)], [], {"object": "pallet A", "at_zone": "chuyền 3"}),
    ("m08_pickdrop_cross", "Nhặt kiện C rồi để ở kho B", "pick/drop", True,
     [("crate-C", "kiện C", 6, 2)],
     [(10, 4), (10, 5)], {"object": "kiện C", "at_zone": "kho B"}),
    ("m09_language_case", "ĐƯA Pallet a TỚI Chuyền 3", "language", True,
     [("pallet-A", "pallet A", 3, 2)], [], {"object": "pallet A", "at_zone": "chuyền 3"}),
    ("m10_infeasible_missing", "Đưa pallet Z tới chuyền 3", "infeasible", False,
     [("pallet-A", "pallet A", 3, 3)], [], {"object": "pallet Z", "at_zone": "chuyền 3"}),
    ("m11_infeasible_enclosed", "Đưa hộp kẹt tới chuyền 3", "infeasible", False,
     [("stuck-X", "hộp kẹt", 5, 5)],
     [(4, 5), (6, 5), (5, 4), (5, 6)], {"object": "hộp kẹt", "at_zone": "chuyền 3"}),
]


def build(spec) -> dict:
    tid, goal, cat, feasible, objs, obs, success = spec
    state = WorldState(
        width=W, height=H, tick=0,
        robot=Entity(id="robot-1", kind="robot", label="Robot", pos=Cell(x=1, y=1)),
        objects=[Entity(id=i, kind="object", label=lb, pos=Cell(x=x, y=y))
                 for (i, lb, x, y) in objs],
        people=[],
        obstacles=[Entity(id=f"obs-{k}", kind="obstacle", pos=Cell(x=x, y=y))
                   for k, (x, y) in enumerate(obs)],
        zones=[{"name": z["name"], "cells": [{"x": x, "y": y} for (x, y) in z["cells"]]}
               for z in ZONES],
    )
    assert_invariants(World(state))  # scenario phải hợp lệ ngay từ đầu
    d = state.model_dump()
    d["task"] = {"id": tid, "goal_text": goal, "category": cat,
                 "feasible": feasible, "success": success, "dynamic": []}
    return d


def main() -> None:
    SCEN_DIR.mkdir(parents=True, exist_ok=True)
    for spec in TASKS:
        d = build(spec)
        path = SCEN_DIR / f"{spec[0]}.json"
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print("wrote", path.name)
    print(f"Total: {len(TASKS)} tasks")


if __name__ == "__main__":
    main()
