"""Automated UI-backend integration test: load every scenario via API and
validate the returned WorldState matches the source JSON file.

This verifies that ALL 33 scenarios render correctly on the web interface
(the frontend fetches the same /api/v1/scenario endpoint).
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"
SCENARIO_DIR = Path(__file__).parent.parent / "eval" / "scenarios"

# Collect all scenario IDs from the filesystem
SCENARIO_IDS = sorted(
    p.stem for p in SCENARIO_DIR.glob("*.json") if p.stem != "SPEC"
)


def _load_source(scenario_id: str) -> dict:
    """Load the raw JSON scenario file."""
    with open(SCENARIO_DIR / f"{scenario_id}.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def client():
    """httpx client that reuses connections across all tests in this module."""
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c


@pytest.fixture(scope="module")
def catalog(client):
    """Fetch the scenario catalog once."""
    resp = client.get("/api/v1/scenarios")
    assert resp.status_code == 200, f"Catalog fetch failed: {resp.status_code}"
    return resp.json()


# ---------------------------------------------------------------------------
# 1. Catalog completeness
# ---------------------------------------------------------------------------

def test_catalog_has_all_scenarios(catalog):
    """The /api/v1/scenarios endpoint must list all 33 scenario files."""
    api_ids = {s["id"] for s in catalog["scenarios"]}
    file_ids = set(SCENARIO_IDS)
    missing = file_ids - api_ids
    extra = api_ids - file_ids
    assert not missing, f"Scenarios missing from catalog: {missing}"
    assert not extra, f"Extra scenarios in catalog not on disk: {extra}"
    assert len(catalog["scenarios"]) == 33, (
        f"Expected 33 scenarios, got {len(catalog['scenarios'])}"
    )


def test_catalog_has_eval_quick_chips(catalog):
    """8 quick-eval chips must be present."""
    assert len(catalog["eval_quick"]) == 8


def test_catalog_groups(catalog):
    """Every scenario must belong to one of demo / eval_v2 / eval_v1."""
    valid_groups = {"demo", "eval_v2", "eval_v1"}
    for s in catalog["scenarios"]:
        assert s["group"] in valid_groups, f"{s['id']} has invalid group {s['group']}"


def test_catalog_goal_text_not_empty(catalog):
    """Every scenario in the catalog must have a non-empty goal_text."""
    for s in catalog["scenarios"]:
        assert s.get("goal_text"), f"{s['id']} has empty goal_text"


# ---------------------------------------------------------------------------
# 2. Per-scenario load & validation (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_load_scenario(client, scenario_id):
    """POST /api/v1/scenario?name=<id> must return 200 with matching data."""
    resp = client.post(f"/api/v1/scenario?name={scenario_id}")
    assert resp.status_code == 200, (
        f"Failed to load scenario '{scenario_id}': HTTP {resp.status_code}"
    )
    data = resp.json()
    source = _load_source(scenario_id)

    # Grid dimensions
    assert data["width"] == source["width"], (
        f"{scenario_id}: width mismatch {data['width']} != {source['width']}"
    )
    assert data["height"] == source["height"], (
        f"{scenario_id}: height mismatch {data['height']} != {source['height']}"
    )

    # Robot position
    assert data["robot"]["pos"]["x"] == source["robot"]["pos"]["x"], (
        f"{scenario_id}: robot x mismatch"
    )
    assert data["robot"]["pos"]["y"] == source["robot"]["pos"]["y"], (
        f"{scenario_id}: robot y mismatch"
    )

    # Object count
    assert len(data["objects"]) == len(source["objects"]), (
        f"{scenario_id}: objects count {len(data['objects'])} != {len(source['objects'])}"
    )

    # Object labels match
    src_labels = sorted(o.get("label", "") or "" for o in source["objects"])
    api_labels = sorted(o.get("label", "") or "" for o in data["objects"])
    assert src_labels == api_labels, (
        f"{scenario_id}: object labels mismatch: {api_labels} != {src_labels}"
    )

    # Object positions
    src_obj_pos = sorted((o["pos"]["x"], o["pos"]["y"]) for o in source["objects"])
    api_obj_pos = sorted((o["pos"]["x"], o["pos"]["y"]) for o in data["objects"])
    assert src_obj_pos == api_obj_pos, (
        f"{scenario_id}: object positions mismatch"
    )

    # People count
    assert len(data["people"]) == len(source.get("people", [])), (
        f"{scenario_id}: people count mismatch"
    )

    # People positions
    if source.get("people"):
        src_ppl_pos = sorted((p["pos"]["x"], p["pos"]["y"]) for p in source["people"])
        api_ppl_pos = sorted((p["pos"]["x"], p["pos"]["y"]) for p in data["people"])
        assert src_ppl_pos == api_ppl_pos, (
            f"{scenario_id}: people positions mismatch"
        )

    # Obstacle count
    assert len(data["obstacles"]) == len(source.get("obstacles", [])), (
        f"{scenario_id}: obstacles count {len(data['obstacles'])} != {len(source.get('obstacles', []))}"
    )

    # Obstacle positions
    if source.get("obstacles"):
        src_obs_pos = sorted((o["pos"]["x"], o["pos"]["y"]) for o in source["obstacles"])
        api_obs_pos = sorted((o["pos"]["x"], o["pos"]["y"]) for o in data["obstacles"])
        assert src_obs_pos == api_obs_pos, (
            f"{scenario_id}: obstacle positions mismatch"
        )

    # Zone count
    assert len(data["zones"]) == len(source.get("zones", [])), (
        f"{scenario_id}: zones count mismatch"
    )

    # Zone names
    src_zone_names = sorted(z["name"] for z in source.get("zones", []))
    api_zone_names = sorted(z["name"] for z in data["zones"])
    assert src_zone_names == api_zone_names, (
        f"{scenario_id}: zone names mismatch: {api_zone_names} != {src_zone_names}"
    )


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_scenario_zones_cell_count(client, scenario_id):
    """Each zone must have the correct number of cells."""
    resp = client.post(f"/api/v1/scenario?name={scenario_id}")
    data = resp.json()
    source = _load_source(scenario_id)

    src_zones = {z["name"]: len(z["cells"]) for z in source.get("zones", [])}
    api_zones = {z["name"]: len(z["cells"]) for z in data["zones"]}
    assert src_zones == api_zones, (
        f"{scenario_id}: zone cell counts mismatch: {api_zones} != {src_zones}"
    )


# ---------------------------------------------------------------------------
# 3. Verify the world GET endpoint after loading each scenario
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_get_world_after_load(client, scenario_id):
    """After loading a scenario, GET /api/v1/world must return matching state."""
    client.post(f"/api/v1/scenario?name={scenario_id}")
    resp = client.get("/api/v1/world")
    assert resp.status_code == 200
    data = resp.json()
    source = _load_source(scenario_id)

    assert data["width"] == source["width"]
    assert data["height"] == source["height"]
    assert data["robot"]["pos"]["x"] == source["robot"]["pos"]["x"]
    assert data["robot"]["pos"]["y"] == source["robot"]["pos"]["y"]
    assert len(data["objects"]) == len(source["objects"])
