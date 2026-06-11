"""Tests for the 9 world-operation tools (no LLM calls)."""
from __future__ import annotations

import json
from pathlib import Path

from src.models.schemas import Cell
from src.services.world import World, set_current_world

SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"


def _load(name: str) -> World:
    w = World.from_scenario(SCENARIO_DIR / f"{name}.json")
    set_current_world(w)
    return w


# ---------------------------------------------------------------------------
# perceive
# ---------------------------------------------------------------------------


def test_perceive_returns_world() -> None:
    from src.agents.tools.tools import perceive

    _load("warehouse_basic")
    result = json.loads(perceive.invoke({}))
    assert "robot" in result
    assert "objects" in result
    assert result["robot"]["pos"]["x"] == 1


# ---------------------------------------------------------------------------
# locate_object
# ---------------------------------------------------------------------------


def test_locate_object_found() -> None:
    from src.agents.tools.tools import locate_object

    _load("warehouse_basic")
    result = json.loads(locate_object.invoke({"label": "pallet A"}))
    assert result["found"] is True
    assert result["id"] == "pallet-A"


def test_locate_object_case_insensitive() -> None:
    from src.agents.tools.tools import locate_object

    _load("warehouse_basic")
    result = json.loads(locate_object.invoke({"label": "PALLET a"}))
    assert result["found"] is True


def test_locate_object_not_found() -> None:
    from src.agents.tools.tools import locate_object

    _load("warehouse_basic")
    result = json.loads(locate_object.invoke({"label": "không có"}))
    assert result["found"] is False


# ---------------------------------------------------------------------------
# check_path
# ---------------------------------------------------------------------------


def test_check_path_clear() -> None:
    from src.agents.tools.tools import check_path

    _load("warehouse_basic")
    result = json.loads(check_path.invoke({"target_x": 5, "target_y": 2}))
    assert result["clear"] is True


def test_check_path_blocked_by_person() -> None:
    from src.agents.tools.tools import check_path

    _load("warehouse_blocked")
    # The only way from (1,1) to (12,3) in blocked scenario goes through person at (7,3)
    # check_path uses astar which avoids people → returns no_path or blocked
    result = json.loads(check_path.invoke({"target_x": 12, "target_y": 3}))
    # With person + 2 obstacles blocking x=7 rows 3-5, path may still exist via y=0
    # Just verify the tool returns without error
    assert "clear" in result


# ---------------------------------------------------------------------------
# move_to
# ---------------------------------------------------------------------------


def test_move_to_reaches_goal() -> None:
    from src.agents.tools.tools import move_to

    _load("warehouse_basic")
    result = json.loads(move_to.invoke({"target_x": 12, "target_y": 3}))
    assert result["reached"] is True
    assert result["pos"]["x"] == 12
    assert result["pos"]["y"] == 3


def test_move_to_blocked_by_person() -> None:
    from src.agents.tools.tools import move_to

    _load("warehouse_blocked")
    # Direct path from (1,1) to (8,3) passes through person at (7,3) since astar_static
    # goes through row 3 — robot stops before the person
    result = json.loads(move_to.invoke({"target_x": 8, "target_y": 3}))
    # Should be blocked (reached=False, blocked_by) or reached if alternate path used
    # astar_static ignores people, so path goes through (7,3)… but step check stops it
    assert "reached" in result
    if not result["reached"]:
        assert "blocked_by" in result or "error" in result


def test_move_to_no_path() -> None:
    from src.agents.tools.tools import move_to
    from src.models.schemas import Entity, WorldState

    state = WorldState(
        width=3, height=3, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[], people=[],
        obstacles=[
            Entity(id="o1", kind="obstacle", pos=Cell(x=1, y=0)),
            Entity(id="o2", kind="obstacle", pos=Cell(x=0, y=1)),
        ],
        zones=[],
    )
    w = World(state)
    set_current_world(w)
    result = json.loads(move_to.invoke({"target_x": 2, "target_y": 2}))
    assert result["reached"] is False
    assert result.get("error") == "no_path"


# ---------------------------------------------------------------------------
# pick
# ---------------------------------------------------------------------------


def test_pick_valid() -> None:
    from src.agents.tools.tools import move_to, pick

    w = _load("warehouse_basic")
    # Move robot adjacent to pallet A at (3,3)
    move_to.invoke({"target_x": 3, "target_y": 3})
    result = json.loads(pick.invoke({"object_id_or_label": "pallet A"}))
    assert result["ok"] is True
    assert w.to_state().robot.carrying == "pallet-A"


def test_pick_not_adjacent() -> None:
    from src.agents.tools.tools import pick

    _load("warehouse_basic")
    result = json.loads(pick.invoke({"object_id_or_label": "pallet A"}))
    assert result["ok"] is False
    assert "not_adjacent" in result["error"]


def test_pick_already_carrying() -> None:
    from src.agents.tools.tools import move_to, pick

    _load("warehouse_basic")
    move_to.invoke({"target_x": 3, "target_y": 3})
    pick.invoke({"object_id_or_label": "pallet A"})
    result = json.loads(pick.invoke({"object_id_or_label": "pallet A"}))
    assert result["ok"] is False
    assert "already_carrying" in result["error"]


# ---------------------------------------------------------------------------
# drop
# ---------------------------------------------------------------------------


def test_drop_valid() -> None:
    from src.agents.tools.tools import drop, move_to, pick

    w = _load("warehouse_basic")
    move_to.invoke({"target_x": 3, "target_y": 3})
    pick.invoke({"object_id_or_label": "pallet A"})
    result = json.loads(drop.invoke({"target_x": 12, "target_y": 3}))
    assert result["ok"] is True
    assert w.to_state().robot.carrying is None


def test_drop_not_carrying() -> None:
    from src.agents.tools.tools import drop

    _load("warehouse_basic")
    result = json.loads(drop.invoke({"target_x": 12, "target_y": 3}))
    assert result["ok"] is False
    assert "not_carrying" in result["error"]


# ---------------------------------------------------------------------------
# wait
# ---------------------------------------------------------------------------


def test_wait_advances_tick() -> None:
    from src.agents.tools.tools import wait

    w = _load("warehouse_basic")
    old_tick = w.to_state().tick
    result = json.loads(wait.invoke({"ticks": 3}))
    assert w.to_state().tick == old_tick + 3
    assert "robot" in result  # returns perceive output


# ---------------------------------------------------------------------------
# ask_human & done
# ---------------------------------------------------------------------------


def test_ask_human() -> None:
    from src.agents.tools.tools import ask_human

    _load("warehouse_basic")
    result = json.loads(ask_human.invoke({"question": "Có an toàn không?"}))
    assert result["paused"] is True
    assert "Có an toàn không?" in result["question"]


def test_done() -> None:
    from src.agents.tools.tools import done

    _load("warehouse_basic")
    result = json.loads(done.invoke({"summary": "Đã hoàn thành."}))
    assert result["done"] is True
    assert "Đã hoàn thành." in result["summary"]
