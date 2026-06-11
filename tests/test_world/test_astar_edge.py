"""S3 — A* đúng ở các ca biên (PLAN_thu_nho_162.md)."""
from __future__ import annotations

from src.models.schemas import Cell, Entity, WorldState
from src.services.world import World


def _open(w: int = 6, h: int = 6, obstacles=None) -> World:
    return World(WorldState(
        width=w, height=h, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=0, y=0)),
        objects=[], people=[],
        obstacles=[Entity(id=f"o{i}", kind="obstacle", pos=Cell(x=c[0], y=c[1]))
                   for i, c in enumerate(obstacles or [])],
        zones=[],
    ))


def test_same_start_goal_static() -> None:
    assert _open().astar_static(Cell(x=2, y=2), Cell(x=2, y=2)) == [Cell(x=2, y=2)]


def test_goal_out_of_bounds_returns_none() -> None:
    w = _open()
    assert w.astar(Cell(x=0, y=0), Cell(x=99, y=99)) is None
    assert w.astar_static(Cell(x=0, y=0), Cell(x=-1, y=0)) is None


def test_optimal_length_open_grid() -> None:
    p = _open().astar(Cell(x=0, y=0), Cell(x=4, y=3))
    assert p is not None
    assert len(p) == (4 + 3) + 1
    for a, b in zip(p, p[1:]):
        assert abs(a.x - b.x) + abs(a.y - b.y) == 1


def test_enclosed_goal_returns_none() -> None:
    w = _open(obstacles=[(1, 2), (3, 2), (2, 1), (2, 3)])
    assert w.astar(Cell(x=0, y=0), Cell(x=2, y=2)) is None


def test_path_avoids_obstacles() -> None:
    w = _open(obstacles=[(2, 0), (2, 1)])
    p = w.astar(Cell(x=0, y=0), Cell(x=4, y=0))
    assert p is not None
    assert all((c.x, c.y) not in {(2, 0), (2, 1)} for c in p)
