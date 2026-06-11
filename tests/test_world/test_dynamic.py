"""Tests for dynamic people movement and WorldState.task field."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.models.schemas import Cell
from src.services.world import World

SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"


def test_dynamic_person_moves_on_tick() -> None:
    """advance_tick applies dynamic events at the correct tick."""
    w = World.from_scenario(SCENARIO_DIR / "warehouse_dynamic.json")
    assert w.to_state().tick == 0
    person = w.to_state().people[0]
    start_pos = (person.pos.x, person.pos.y)

    w.advance_tick(2)

    person_after = w.to_state().people[0]
    assert (person_after.pos.x, person_after.pos.y) == (7, 3)
    assert (person_after.pos.x, person_after.pos.y) != start_pos


def test_dynamic_person_moves_back_later() -> None:
    """Second dynamic event moves person back at tick 5."""
    w = World.from_scenario(SCENARIO_DIR / "warehouse_dynamic.json")
    w.advance_tick(5)
    person = w.to_state().people[0]
    assert (person.pos.x, person.pos.y) == (2, 8)


def test_dynamic_event_only_applies_once() -> None:
    """Event at tick 2 should not re-apply when advancing past tick 2 again."""
    w = World.from_scenario(SCENARIO_DIR / "warehouse_dynamic.json")
    w.advance_tick(2)
    pos_after_2 = (w.to_state().people[0].pos.x, w.to_state().people[0].pos.y)
    w.advance_tick(1)  # tick 3, no event
    pos_after_3 = (w.to_state().people[0].pos.x, w.to_state().people[0].pos.y)
    assert pos_after_2 == pos_after_3  # no change at tick 3


def test_no_dynamic_without_task() -> None:
    """World without task block has empty dynamic list — advance_tick is safe."""
    w = World.from_scenario(SCENARIO_DIR / "warehouse_basic.json")
    w.advance_tick(10)  # must not raise
    assert w.to_state().tick == 10


def test_wait_then_path_clear() -> None:
    """After person moves away (tick 5), path to (7,3) should be passable."""
    w = World.from_scenario(SCENARIO_DIR / "warehouse_dynamic.json")
    w.advance_tick(2)  # person moves to (7,3)
    assert w.is_blocked(Cell(x=7, y=3))  # blocked by person

    w.advance_tick(3)  # tick 5: person moves back to (2,8)
    assert not w.is_blocked(Cell(x=7, y=3))  # now clear


@pytest.mark.parametrize("scenario_name", ["warehouse_basic", "warehouse_blocked", "warehouse_dynamic"])
def test_task_field_is_optional(scenario_name: str) -> None:
    w = World.from_scenario(SCENARIO_DIR / f"{scenario_name}.json")
    state = w.to_state()
    assert state.tick >= 0
