"""S2 — bất biến trạng thái + xác thực drop_at (PLAN_thu_nho_162.md)."""
from __future__ import annotations

import glob
from pathlib import Path

import pytest

from src.models.schemas import Cell, Entity, WorldState
from src.services.invariants import InvariantError, assert_invariants
from src.services.world import World

SCEN_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"
BASIC = SCEN_DIR / "warehouse_basic.json"
ALL_SCENARIOS = sorted(glob.glob(str(SCEN_DIR / "*.json")))


def _free_world() -> World:
    return World(WorldState(
        width=5, height=5, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[Entity(id="o1", kind="object", label="hộp", pos=Cell(x=2, y=2))],
        people=[], obstacles=[], zones=[],
    ))


def _state(**kw) -> WorldState:
    base = dict(
        width=5, height=5, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[], people=[], obstacles=[], zones=[],
    )
    base.update(kw)
    return WorldState(**base)


@pytest.mark.parametrize("path", ALL_SCENARIOS, ids=lambda p: Path(p).stem)
def test_shipped_scenarios_satisfy_invariants(path: str) -> None:
    assert_invariants(World.from_scenario(path))


def test_pick_then_drop_preserve_invariants() -> None:
    w = _free_world()
    w.move_robot_to(Cell(x=2, y=2))
    assert w.pick_object("hộp")["ok"]
    assert_invariants(w)
    assert w.drop_at(Cell(x=4, y=4))["ok"]
    assert_invariants(w)


def test_drop_rejects_out_of_bounds() -> None:
    w = _free_world()
    w.move_robot_to(Cell(x=2, y=2))
    w.pick_object("hộp")
    res = w.drop_at(Cell(x=-1, y=0))
    assert res["ok"] is False and res["error"] == "out_of_bounds"
    assert w.to_state().robot.carrying == "o1"


def test_drop_rejects_obstacle() -> None:
    w = World(WorldState(
        width=5, height=5, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[Entity(id="o1", kind="object", label="hộp", pos=Cell(x=1, y=0))],
        people=[],
        obstacles=[Entity(id="ob", kind="obstacle", pos=Cell(x=2, y=2))],
        zones=[],
    ))
    w.move_robot_to(Cell(x=1, y=0))
    w.pick_object("hộp")
    res = w.drop_at(Cell(x=2, y=2))
    assert res["ok"] is False and res["error"] == "blocked_obstacle"
    assert w.to_state().robot.carrying == "o1"


def test_detect_robot_out_of_bounds() -> None:
    with pytest.raises(InvariantError):
        assert_invariants(_state(robot=Entity(id="r", kind="robot", pos=Cell(x=9, y=9))))


def test_detect_carrying_but_object_on_grid() -> None:
    with pytest.raises(InvariantError):
        assert_invariants(_state(
            robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0), carrying="o1"),
            objects=[Entity(id="o1", kind="object", pos=Cell(x=2, y=2))],
        ))


def test_detect_offgrid_without_carrying() -> None:
    with pytest.raises(InvariantError):
        assert_invariants(_state(objects=[Entity(id="o1", kind="object", pos=Cell(x=-1, y=-1))]))


def test_detect_object_on_obstacle() -> None:
    with pytest.raises(InvariantError):
        assert_invariants(_state(
            objects=[Entity(id="o1", kind="object", pos=Cell(x=2, y=2))],
            obstacles=[Entity(id="ob", kind="obstacle", pos=Cell(x=2, y=2))],
        ))


def test_valid_state_passes() -> None:
    assert_invariants(World.from_scenario(BASIC))
