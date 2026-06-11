"""State invariants cho sim kho 2D (S2 trong PLAN_thu_nho_162.md).

`assert_invariants()` mã hoá các thuộc tính LUÔN phải đúng sau mọi mutation của
World. Hàm cố tình **tách rời** khỏi nội bộ World: nó chỉ đọc `WorldState`
serialisable, nên dùng lại được ở test, eval harness, và như một post-condition
guard ngay trong các mutation của World.

Bất biến lõi (phạm vi "di chuyển 1 vật thể"):
  1. Lưới hợp lệ (width/height > 0, tick >= 0).
  2. Robot trong lưới và KHÔNG nằm trên obstacle tĩnh.
  3. Nhất quán "đang mang":
       - carrying = None  ⇒  KHÔNG vật nào off-grid.
       - carrying = id    ⇒  đúng MỘT vật off-grid, và đó chính là vật id,
                              với pos == (-1, -1).
  4. Mọi vật on-grid: trong lưới và KHÔNG nằm trên obstacle.
  5. Mọi người: trong lưới (người là phần ngoài lõi nên chỉ kiểm in-bounds).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # tránh import vòng — chỉ cần cho type hint
    from src.models.schemas import WorldState
    from src.services.world import World

OFFGRID = (-1, -1)


class InvariantError(AssertionError):
    """Ném ra khi world rơi vào trạng thái bất khả thi về mặt logic."""


def _state_of(world_or_state: World | WorldState) -> WorldState:
    """Chấp nhận cả World (có .to_state()) lẫn WorldState trực tiếp."""
    to_state = getattr(world_or_state, "to_state", None)
    return to_state() if callable(to_state) else world_or_state  # type: ignore[return-value]


def assert_invariants(world: World | WorldState) -> None:
    """Ném InvariantError nếu world vi phạm bất kỳ bất biến lõi nào."""
    s = _state_of(world)

    # 1. Sanity lưới
    if s.width <= 0 or s.height <= 0:
        raise InvariantError(f"kích thước lưới phải dương: {s.width}x{s.height}")
    if s.tick < 0:
        raise InvariantError(f"tick âm: {s.tick}")

    def in_bounds(p) -> bool:
        return 0 <= p.x < s.width and 0 <= p.y < s.height

    def is_offgrid(p) -> bool:
        return p.x < 0 or p.y < 0

    obstacle_cells = {(o.pos.x, o.pos.y) for o in s.obstacles}

    # 2. Robot
    if not in_bounds(s.robot.pos):
        raise InvariantError(f"robot ngoài lưới: {s.robot.pos}")
    if (s.robot.pos.x, s.robot.pos.y) in obstacle_cells:
        raise InvariantError(f"robot nằm trên obstacle: {s.robot.pos}")

    # 3. Nhất quán "đang mang"
    offgrid_objs = [o for o in s.objects if is_offgrid(o.pos)]
    carrying = s.robot.carrying
    if carrying is None:
        if offgrid_objs:
            raise InvariantError(
                f"không mang gì nhưng có vật off-grid: {[o.id for o in offgrid_objs]}"
            )
    else:
        held = [o for o in s.objects if o.id == carrying]
        if not held:
            raise InvariantError(
                f"carrying='{carrying}' nhưng không tồn tại vật đó"
            )
        if len(offgrid_objs) != 1 or offgrid_objs[0].id != carrying:
            raise InvariantError(
                f"vật off-grid phải đúng là vật đang mang ('{carrying}'); "
                f"off-grid hiện tại: {[o.id for o in offgrid_objs]}"
            )
        if (held[0].pos.x, held[0].pos.y) != OFFGRID:
            raise InvariantError(
                f"vật đang mang phải ở {OFFGRID}, đang ở {held[0].pos}"
            )

    # 4. Vật on-grid
    for o in s.objects:
        if is_offgrid(o.pos):
            continue  # vật đang mang — đã kiểm ở mục 3
        if not in_bounds(o.pos):
            raise InvariantError(f"vật '{o.id}' ngoài lưới: {o.pos}")
        if (o.pos.x, o.pos.y) in obstacle_cells:
            raise InvariantError(f"vật '{o.id}' nằm trên obstacle: {o.pos}")

    # 5. Người (ngoài lõi — chỉ kiểm in-bounds)
    for p in s.people:
        if not in_bounds(p.pos):
            raise InvariantError(f"người '{p.id}' ngoài lưới: {p.pos}")
