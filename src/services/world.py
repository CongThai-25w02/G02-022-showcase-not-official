from __future__ import annotations

import heapq
import json
import unicodedata
from pathlib import Path

from src.models.schemas import Cell, Entity, WorldState, Zone  # noqa: F401
from src.services.invariants import assert_invariants


class World:
    def __init__(self, state: WorldState, check_invariants: bool = True) -> None:
        self._state = state
        self._dynamic: list[dict] = (state.task or {}).get("dynamic", [])
        self._check_invariants = check_invariants
        # Tổng số ô robot đã đi (cho metric SPL). Thuần đo lường, không đổi hành vi.
        self._distance_traveled = 0

    @property
    def distance_traveled(self) -> int:
        """Tổng số ô robot thực sự di chuyển (dùng tính SPL/path-efficiency)."""
        return self._distance_traveled

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_scenario(
        cls, path_or_dict: str | Path | dict, check_invariants: bool = True
    ) -> World:
        if isinstance(path_or_dict, dict):
            state = WorldState.model_validate(path_or_dict)
        else:
            with open(path_or_dict, encoding="utf-8") as f:
                data = json.load(f)
            state = WorldState.model_validate(data)
        return cls(state, check_invariants=check_invariants)

    # ------------------------------------------------------------------
    # State access
    # ------------------------------------------------------------------

    def to_state(self) -> WorldState:
        return self._state

    def to_snapshot(self) -> dict:
        """Minimal snapshot for frontend animation: robot pos/carrying, people positions, tick."""
        return {
            "robot": {
                "pos": self._state.robot.pos.model_dump(),
                "carrying": self._state.robot.carrying,
            },
            "people": [
                {"id": p.id, "pos": p.pos.model_dump()}
                for p in self._state.people
            ],
            "tick": self._state.tick,
        }

    # ------------------------------------------------------------------
    # Geometry helpers (read-only)
    # ------------------------------------------------------------------

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell.x < self._state.width and 0 <= cell.y < self._state.height

    def is_blocked_static(self, cell: Cell) -> bool:
        """Blocked by static obstacles or out of bounds (ignores people)."""
        if not self.in_bounds(cell):
            return True
        return any(e.pos.x == cell.x and e.pos.y == cell.y for e in self._state.obstacles)

    def is_blocked(self, cell: Cell) -> bool:
        """Blocked by obstacles, people, or out of bounds."""
        if not self.in_bounds(cell):
            return True
        blockers = self._state.obstacles + self._state.people
        return any(e.pos.x == cell.x and e.pos.y == cell.y for e in blockers)

    def neighbors(self, cell: Cell) -> list[Cell]:
        candidates = [
            Cell(x=cell.x + 1, y=cell.y),
            Cell(x=cell.x - 1, y=cell.y),
            Cell(x=cell.x, y=cell.y + 1),
            Cell(x=cell.x, y=cell.y - 1),
        ]
        return [c for c in candidates if not self.is_blocked(c)]

    def _astar_impl(self, start: Cell, goal: Cell, blocked_fn) -> list[Cell] | None:
        if blocked_fn(goal):
            return None
        if start.x == goal.x and start.y == goal.y:
            return [start]

        def h(c: Cell) -> int:
            return abs(c.x - goal.x) + abs(c.y - goal.y)

        open_heap: list[tuple[int, int, tuple[int, int]]] = [
            (h(start), 0, (start.x, start.y))
        ]
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], int] = {(start.x, start.y): 0}

        while open_heap:
            _f, g, (cx, cy) = heapq.heappop(open_heap)

            if cx == goal.x and cy == goal.y:
                path: list[Cell] = []
                node: tuple[int, int] = (cx, cy)
                while node in came_from:
                    path.append(Cell(x=node[0], y=node[1]))
                    node = came_from[node]
                path.append(start)
                path.reverse()
                return path

            if g > g_score.get((cx, cy), 10**9):
                continue

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = Cell(x=cx + dx, y=cy + dy)
                if blocked_fn(nb):
                    continue
                key = (nb.x, nb.y)
                new_g = g + 1
                if new_g < g_score.get(key, 10**9):
                    g_score[key] = new_g
                    came_from[key] = (cx, cy)
                    heapq.heappush(open_heap, (new_g + h(nb), new_g, key))

        return None

    def astar(self, start: Cell, goal: Cell) -> list[Cell] | None:
        """A* avoiding obstacles + people."""
        return self._astar_impl(start, goal, self.is_blocked)

    def astar_static(self, start: Cell, goal: Cell) -> list[Cell] | None:
        """A* avoiding only static obstacles (ignores people)."""
        return self._astar_impl(start, goal, self.is_blocked_static)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def find_object(self, label: str) -> Entity | None:
        for obj in self._state.objects:
            if obj.label == label:
                return obj
        return None

    def find_object_fuzzy(self, label: str) -> Entity | None:
        """Case-insensitive, accent-stripped match."""
        needle = _normalize(label)
        for obj in self._state.objects:
            if obj.label and _normalize(obj.label) == needle:
                return obj
        return None

    def zone_cells(self, name: str) -> list[Cell]:
        for zone in self._state.zones:
            if zone.name == name:
                return zone.cells
        return []

    def person_at(self, cell: Cell) -> Entity | None:
        for p in self._state.people:
            if p.pos.x == cell.x and p.pos.y == cell.y:
                return p
        return None

    def relative_position(self, cell: Cell) -> str:
        rx, ry = self._state.robot.pos.x, self._state.robot.pos.y
        dx, dy = cell.x - rx, cell.y - ry
        h_dir = "phải" if dx >= 0 else "trái"
        v_dir = "xa" if abs(dx) + abs(dy) > 4 else "gần"
        return f"{h_dir}, {v_dir}"

    def cell_zone(self, cell: Cell) -> str | None:
        for zone in self._state.zones:
            if any(c.x == cell.x and c.y == cell.y for c in zone.cells):
                return zone.name
        return None

    # ------------------------------------------------------------------
    # Invariant guard
    # ------------------------------------------------------------------

    def _verify(self) -> None:
        """Tự kiểm bất biến lõi sau mutation (PLAN_thu_nho_162.md S2)."""
        if self._check_invariants:
            assert_invariants(self)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def move_robot_to(self, target: Cell) -> dict:
        """Move robot step-by-step along astar_static path.

        Stops immediately if the next cell is occupied by a person.
        Returns {reached, pos, blocked_by?, error?}.
        """
        start_pos = self._state.robot.pos.model_dump()
        path = self.astar_static(self._state.robot.pos, target)
        if path is None:
            return {"reached": False, "error": "no_path", "pos": start_pos}

        for step in path[1:]:
            person = self.person_at(step)
            if person is not None:
                self._verify()
                return {
                    "reached": False,
                    "blocked_by": person.model_dump(),
                    "pos": self._state.robot.pos.model_dump(),
                    "start_pos": start_pos,
                }
            self._state.robot.pos = step
            self._distance_traveled += 1

        self._verify()
        return {"reached": True, "pos": self._state.robot.pos.model_dump()}

    def pick_object(self, id_or_label: str) -> dict:
        """Pick up an object adjacent to or on the robot's cell."""
        if self._state.robot.carrying is not None:
            return {"ok": False, "error": "already_carrying"}

        obj = self._find_entity(id_or_label)
        if obj is None:
            return {"ok": False, "error": f"object_not_found: {id_or_label}"}

        rp = self._state.robot.pos
        op = obj.pos
        dist = abs(rp.x - op.x) + abs(rp.y - op.y)
        if dist > 1:
            return {"ok": False, "error": "not_adjacent"}

        self._state.robot.carrying = obj.id
        # Mark object as carried by moving it off-grid
        obj.pos = Cell(x=-1, y=-1)
        self._verify()
        return {"ok": True, "carrying": obj.id}

    def drop_at(self, target: Cell) -> dict:
        """Drop carried object at target cell.

        Validates the target so the sim never reaches an invalid state
        (PLAN_thu_nho_162.md S4): no dropping out of bounds or onto a static
        obstacle. Returns an explicit error instead of corrupting the world.
        """
        if self._state.robot.carrying is None:
            return {"ok": False, "error": "not_carrying"}
        if not self.in_bounds(target):
            return {"ok": False, "error": "out_of_bounds"}
        if self.is_blocked_static(target):
            return {"ok": False, "error": "blocked_obstacle"}

        obj_id = self._state.robot.carrying
        obj = next((o for o in self._state.objects if o.id == obj_id), None)
        if obj is None:
            return {"ok": False, "error": "carried_object_missing"}

        obj.pos = target
        self._state.robot.carrying = None
        self._verify()
        return {"ok": True, "dropped": obj_id, "at": target.model_dump()}

    def advance_tick(self, n: int = 1) -> None:
        old_tick = self._state.tick
        self._state.tick += n
        for event in self._dynamic:
            t = event.get("tick")
            if t is not None and old_tick < t <= self._state.tick:
                self._apply_dynamic_event(event)

    def _apply_dynamic_event(self, event: dict) -> None:
        person_id = event.get("person")
        target = event.get("to")
        if not person_id or not target:
            return
        for person in self._state.people:
            if person.id == person_id:
                person.pos = Cell(x=target["x"], y=target["y"])
                break

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_entity(self, id_or_label: str) -> Entity | None:
        needle = _normalize(id_or_label)
        for obj in self._state.objects:
            if obj.id == id_or_label:
                return obj
            if obj.label and _normalize(obj.label) == needle:
                return obj
        return None


# ---------------------------------------------------------------------------
# String normalisation helper
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    return unicodedata.normalize("NFC", s).casefold().strip()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_current_world: World | None = None

_DEFAULT_SCENARIO = (
    Path(__file__).parent.parent.parent / "eval" / "scenarios" / "warehouse_basic.json"
)


def get_current_world() -> World:
    global _current_world
    if _current_world is None:
        _current_world = World.from_scenario(_DEFAULT_SCENARIO)
    return _current_world


def set_current_world(world: World) -> None:
    global _current_world
    _current_world = world
