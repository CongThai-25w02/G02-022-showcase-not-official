"""S1/S2 — property-based: chuỗi action hợp lệ luôn bảo toàn bất biến.

Hypothesis sinh ngẫu nhiên world (lưới + obstacle + vật, không người) và một
chuỗi action (move/pick/drop, kể cả đích ngoài lưới / vật không tồn tại). Sau
mỗi bước, bất biến lõi phải vẫn đúng — mutation không bao giờ làm hỏng world.
"""
from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.schemas import Cell, Entity, WorldState
from src.services.invariants import assert_invariants
from src.services.world import World


@st.composite
def world_and_actions(draw):
    w = draw(st.integers(min_value=3, max_value=6))
    h = draw(st.integers(min_value=3, max_value=6))
    all_cells = [(x, y) for x in range(w) for y in range(h)]
    perm = draw(st.permutations(all_cells))

    n_obs = draw(st.integers(min_value=0, max_value=3))
    n_obj = draw(st.integers(min_value=1, max_value=2))
    robot_xy = perm[0]
    obstacles = list(perm[1:1 + n_obs])
    objects = list(perm[1 + n_obs:1 + n_obs + n_obj])

    state = WorldState(
        width=w, height=h, tick=0,
        robot=Entity(id="r", kind="robot", pos=Cell(x=robot_xy[0], y=robot_xy[1])),
        objects=[Entity(id=f"obj{i}", kind="object", label=f"vật {i}",
                        pos=Cell(x=c[0], y=c[1])) for i, c in enumerate(objects)],
        people=[],
        obstacles=[Entity(id=f"obs{i}", kind="obstacle", pos=Cell(x=c[0], y=c[1]))
                   for i, c in enumerate(obstacles)],
        zones=[],
    )
    obj_ids = [f"obj{i}" for i in range(len(objects))]

    n = draw(st.integers(min_value=0, max_value=8))
    actions = []
    for _ in range(n):
        kind = draw(st.sampled_from(["move", "pick", "drop"]))
        if kind == "pick":
            actions.append(("pick", draw(st.sampled_from(obj_ids + ["khong-ton-tai"]))))
        else:
            actions.append((kind,
                            draw(st.integers(min_value=-1, max_value=w)),
                            draw(st.integers(min_value=-1, max_value=h))))
    return state, actions


@settings(max_examples=200, deadline=None)
@given(world_and_actions())
def test_random_sequences_preserve_invariants(data) -> None:
    state, actions = data
    w = World(state)            # check_invariants=True -> tự kiểm sau mỗi mutation
    assert_invariants(w)        # trạng thái khởi tạo hợp lệ
    for a in actions:
        if a[0] == "move":
            w.move_robot_to(Cell(x=a[1], y=a[2]))
        elif a[0] == "pick":
            w.pick_object(a[1])
        else:
            w.drop_at(Cell(x=a[1], y=a[2]))
        assert_invariants(w)    # bất biến giữ sau từng bước
