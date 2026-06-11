from pathlib import Path

import pytest

from src.models.schemas import Cell, Entity, WorldState
from src.services.world import World

SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"
BASIC = SCENARIO_DIR / "warehouse_basic.json"
BLOCKED = SCENARIO_DIR / "warehouse_blocked.json"


# ---------------------------------------------------------------------------
# Loading & entity counts
# ---------------------------------------------------------------------------


def test_load_warehouse_basic() -> None:
    world = World.from_scenario(BASIC)
    state = world.to_state()
    assert isinstance(state, WorldState)
    assert state.width == 16
    assert state.height == 10
    assert state.robot.kind == "robot"
    assert state.robot.pos.x == 1
    assert state.robot.pos.y == 1


def test_entity_counts_basic() -> None:
    state = World.from_scenario(BASIC).to_state()
    assert len(state.objects) == 2
    assert len(state.people) == 0
    assert len(state.obstacles) == 2
    assert len(state.zones) == 2


def test_entity_counts_blocked() -> None:
    state = World.from_scenario(BLOCKED).to_state()
    assert len(state.people) == 1
    assert state.people[0].pos.x == 7
    assert state.people[0].pos.y == 3


# ---------------------------------------------------------------------------
# WorldState round-trip serialisation
# ---------------------------------------------------------------------------


def test_worldstate_roundtrip() -> None:
    state = World.from_scenario(BASIC).to_state()
    data = state.model_dump()
    state2 = WorldState.model_validate(data)
    assert state == state2


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def test_in_bounds() -> None:
    world = World.from_scenario(BASIC)
    assert world.in_bounds(Cell(x=0, y=0))
    assert world.in_bounds(Cell(x=15, y=9))
    assert not world.in_bounds(Cell(x=16, y=0))
    assert not world.in_bounds(Cell(x=0, y=10))
    assert not world.in_bounds(Cell(x=-1, y=0))


def test_is_blocked_obstacle() -> None:
    world = World.from_scenario(BASIC)
    assert world.is_blocked(Cell(x=7, y=4))
    assert world.is_blocked(Cell(x=7, y=5))
    assert not world.is_blocked(Cell(x=7, y=3))


def test_is_blocked_person() -> None:
    world = World.from_scenario(BLOCKED)
    assert world.is_blocked(Cell(x=7, y=3))


def test_is_blocked_out_of_bounds() -> None:
    world = World.from_scenario(BASIC)
    assert world.is_blocked(Cell(x=20, y=0))


# ---------------------------------------------------------------------------
# A* pathfinding
# ---------------------------------------------------------------------------


def test_astar_finds_path() -> None:
    world = World.from_scenario(BASIC)
    start = world.to_state().robot.pos
    goal = Cell(x=12, y=3)
    path = world.astar(start, goal)
    assert path is not None
    assert path[0].x == start.x and path[0].y == start.y
    assert path[-1].x == goal.x and path[-1].y == goal.y
    # Every cell in the path must be in bounds and unblocked
    for cell in path:
        assert world.in_bounds(cell)
    # Every step must be unblocked (except the start which is where robot sits)
    for cell in path[1:]:
        assert not world.is_blocked(cell)
    # Consecutive cells must be adjacent (manhattan distance == 1)
    for a, b in zip(path, path[1:]):
        assert abs(a.x - b.x) + abs(a.y - b.y) == 1


def test_astar_avoids_obstacles() -> None:
    """Wall at x=7 except row 0 — path must go around via y=0 or y=6+."""
    world = World.from_scenario(BASIC)
    path = world.astar(Cell(x=1, y=5), Cell(x=12, y=5))
    assert path is not None
    # Must not pass through obstacle cells (7,4) or (7,5)
    blocked_cells = {(7, 4), (7, 5)}
    for cell in path:
        assert (cell.x, cell.y) not in blocked_cells


def test_astar_returns_none_when_goal_blocked() -> None:
    """Goal cell is an obstacle → no path."""
    world = World.from_scenario(BASIC)
    # (7,4) is an obstacle
    result = world.astar(Cell(x=1, y=1), Cell(x=7, y=4))
    assert result is None


def test_astar_returns_none_no_route() -> None:
    """Goal completely surrounded by obstacles at corners of a tiny grid."""
    state = WorldState(
        width=5,
        height=5,
        tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[],
        people=[],
        obstacles=[
            Entity(id="o1", kind="obstacle", pos=Cell(x=3, y=4)),
            Entity(id="o2", kind="obstacle", pos=Cell(x=4, y=3)),
        ],
        zones=[],
    )
    world = World(state)
    # (4,4) is reachable only via (3,4) or (4,3), both blocked
    result = world.astar(Cell(x=0, y=0), Cell(x=4, y=4))
    assert result is None


def test_astar_same_start_goal() -> None:
    world = World.from_scenario(BASIC)
    start = Cell(x=1, y=1)
    result = world.astar(start, start)
    assert result == [start]


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def test_find_object() -> None:
    world = World.from_scenario(BASIC)
    obj = world.find_object("pallet A")
    assert obj is not None
    assert obj.id == "pallet-A"


def test_find_object_missing() -> None:
    world = World.from_scenario(BASIC)
    assert world.find_object("không tồn tại") is None


def test_zone_cells() -> None:
    world = World.from_scenario(BASIC)
    cells = world.zone_cells("khu A")
    assert len(cells) == 9


def test_zone_cells_missing() -> None:
    world = World.from_scenario(BASIC)
    assert world.zone_cells("không có") == []


def test_from_scenario_dict() -> None:
    """from_scenario also accepts a plain dict."""
    import json

    with open(BASIC, encoding="utf-8") as f:
        data = json.load(f)
    world = World.from_scenario(data)
    assert world.to_state().width == 16


# ---------------------------------------------------------------------------
# to_snapshot
# ---------------------------------------------------------------------------


def test_to_snapshot_keys() -> None:
    world = World.from_scenario(BASIC)
    snap = world.to_snapshot()
    assert "robot" in snap
    assert "pos" in snap["robot"]
    assert "carrying" in snap["robot"]
    assert "people" in snap
    assert "tick" in snap


def test_to_snapshot_values_basic() -> None:
    world = World.from_scenario(BASIC)
    snap = world.to_snapshot()
    assert snap["robot"]["pos"] == {"x": 1, "y": 1}
    assert snap["robot"]["carrying"] is None
    assert snap["people"] == []
    assert snap["tick"] == 0


def test_to_snapshot_includes_people() -> None:
    world = World.from_scenario(BLOCKED)
    snap = world.to_snapshot()
    assert len(snap["people"]) == 1
    assert snap["people"][0]["id"] == "person-1"
    assert snap["people"][0]["pos"] == {"x": 7, "y": 3}


@pytest.mark.parametrize("scenario_name", ["warehouse_basic", "warehouse_blocked"])
def test_scenarios_valid_schema(scenario_name: str) -> None:
    path = SCENARIO_DIR / f"{scenario_name}.json"
    world = World.from_scenario(path)
    state = world.to_state()
    assert state.tick >= 0
    assert state.robot.kind == "robot"
