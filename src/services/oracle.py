"""Oracle kiểm chứng ĐỘC LẬP cho task "di chuyển 1 vật thể"
(PLAN_thu_nho_162.md §3).

Eval dùng oracle này để xác nhận world THẬT SỰ đạt mục tiêu, thay vì tin lời
agent tự khai qua `done(summary)`. Oracle chỉ đọc trạng thái world.
"""
from __future__ import annotations

from src.services.world import World, _normalize


def _resolve_object(world: World, key: str):
    """Tìm vật theo nhãn (fuzzy: bỏ dấu, hoa/thường) hoặc theo id."""
    obj = world.find_object_fuzzy(key)
    if obj is not None:
        return obj
    for o in world.to_state().objects:
        if o.id == key:
            return o
    return None


def _dest_cells(world: World, dest) -> set[tuple[int, int]]:
    """Quy `dest` về tập ô (x, y) chấp nhận được.

    `dest` có thể là: Cell, (x, y) tuple/list, hoặc tên zone (str).
    """
    if isinstance(dest, str):
        cells = world.zone_cells(dest)
        if not cells:  # thử khớp zone fuzzy
            needle = _normalize(dest)
            for z in world.to_state().zones:
                if _normalize(z.name) == needle:
                    cells = z.cells
                    break
        return {(c.x, c.y) for c in cells}
    if isinstance(dest, (tuple, list)):
        return {(int(dest[0]), int(dest[1]))}
    return {(int(dest.x), int(dest.y))}  # Cell-like


def object_cell(world: World, object_key: str) -> tuple[int, int] | None:
    """Vị trí (x, y) hiện tại của vật, hoặc None nếu không có / đang được mang."""
    obj = _resolve_object(world, object_key)
    if obj is None or obj.pos.x < 0 or obj.pos.y < 0:
        return None
    return (obj.pos.x, obj.pos.y)


def check_object_moved(world: World, object_key: str, dest) -> bool:
    """True ⟺ vật `object_key` đang nằm tại `dest` VÀ robot không mang gì.

    Độc lập với status tự khai của agent.
    """
    if world.to_state().robot.carrying is not None:
        return False  # vẫn đang mang ⇒ chưa hoàn thành
    cell = object_cell(world, object_key)
    if cell is None:
        return False
    targets = _dest_cells(world, dest)
    return bool(targets) and cell in targets
