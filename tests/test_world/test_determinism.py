"""S1 — tính xác định của sim (PLAN_thu_nho_162.md)."""
from __future__ import annotations

import hashlib
from pathlib import Path

from src.models.schemas import Cell
from src.services.oracle import check_object_moved
from src.services.world import World

BASIC = Path(__file__).parent.parent.parent / "eval" / "scenarios" / "warehouse_basic.json"

SCRIPT = [("move", 3, 3), ("pick", "pallet A"), ("move", 12, 3), ("drop", 12, 3)]


def _apply(w: World, step) -> None:
    if step[0] == "move":
        w.move_robot_to(Cell(x=step[1], y=step[2]))
    elif step[0] == "pick":
        w.pick_object(step[1])
    elif step[0] == "drop":
        w.drop_at(Cell(x=step[1], y=step[2]))


def _hash(w: World) -> str:
    return hashlib.sha256(w.to_state().model_dump_json().encode("utf-8")).hexdigest()


def _run() -> list[str]:
    w = World.from_scenario(BASIC)
    hashes = [_hash(w)]
    for step in SCRIPT:
        _apply(w, step)
        hashes.append(_hash(w))
    return hashes


def test_state_trace_is_deterministic() -> None:
    assert _run() == _run()


def test_script_actually_moves_object() -> None:
    w = World.from_scenario(BASIC)
    for step in SCRIPT:
        _apply(w, step)
    assert check_object_moved(w, "pallet A", (12, 3))


def test_astar_path_deterministic() -> None:
    w = World.from_scenario(BASIC)
    p1 = w.astar(Cell(x=1, y=1), Cell(x=12, y=3))
    p2 = w.astar(Cell(x=1, y=1), Cell(x=12, y=3))
    assert p1 is not None
    assert [(c.x, c.y) for c in p1] == [(c.x, c.y) for c in p2]
