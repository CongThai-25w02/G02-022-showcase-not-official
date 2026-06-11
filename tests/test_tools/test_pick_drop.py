"""S4/S5 — pick/drop mọi nhánh + observation = sự thật (qua tool)."""
from __future__ import annotations

import json
from pathlib import Path

from src.services.world import World, set_current_world

SCEN_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"


def _load(name: str) -> World:
    w = World.from_scenario(SCEN_DIR / f"{name}.json")
    set_current_world(w)
    return w


def test_pick_object_not_found() -> None:
    from src.agents.tools.tools import pick
    _load("warehouse_basic")
    res = json.loads(pick.invoke({"object_id_or_label": "vật ma"}))
    assert res["ok"] is False
    assert "object_not_found" in res["error"]


def test_pick_fuzzy_label_accent_case() -> None:
    from src.agents.tools.tools import move_to, pick
    w = _load("warehouse_basic")
    move_to.invoke({"target_x": 5, "target_y": 6})   # ô của "thùng B"
    res = json.loads(pick.invoke({"object_id_or_label": "THÙNG b"}))
    assert res["ok"] is True
    assert w.to_state().robot.carrying == "box-B"


def test_drop_out_of_bounds() -> None:
    from src.agents.tools.tools import drop, move_to, pick
    _load("warehouse_basic")
    move_to.invoke({"target_x": 3, "target_y": 3})
    pick.invoke({"object_id_or_label": "pallet A"})
    res = json.loads(drop.invoke({"target_x": -1, "target_y": 0}))
    assert res["ok"] is False
    assert res["error"] == "out_of_bounds"


def test_drop_on_obstacle() -> None:
    from src.agents.tools.tools import drop, move_to, pick
    _load("warehouse_basic")
    move_to.invoke({"target_x": 3, "target_y": 3})
    pick.invoke({"object_id_or_label": "pallet A"})
    res = json.loads(drop.invoke({"target_x": 7, "target_y": 4}))   # obstacle
    assert res["ok"] is False
    assert res["error"] == "blocked_obstacle"


def test_perceive_hides_carried_object() -> None:
    from src.agents.tools.tools import move_to, perceive, pick
    _load("warehouse_basic")
    move_to.invoke({"target_x": 3, "target_y": 3})
    pick.invoke({"object_id_or_label": "pallet A"})
    obs = json.loads(perceive.invoke({}))
    ids = [o["id"] for o in obs["objects"]]
    assert "pallet-A" not in ids
    assert obs["robot"]["carrying"] == "pallet-A"


def test_locate_reflects_position_after_drop() -> None:
    from src.agents.tools.tools import drop, locate_object, move_to, pick
    _load("warehouse_basic")
    move_to.invoke({"target_x": 3, "target_y": 3})
    pick.invoke({"object_id_or_label": "pallet A"})
    move_to.invoke({"target_x": 12, "target_y": 3})
    drop.invoke({"target_x": 12, "target_y": 3})
    loc = json.loads(locate_object.invoke({"label": "pallet A"}))
    assert loc["found"] is True
    assert loc["pos"] == {"x": 12, "y": 3}
