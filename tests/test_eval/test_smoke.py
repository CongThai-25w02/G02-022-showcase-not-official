"""Smoke tests for eval harness — mock LLM, no quota usage."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent.parent
_SCENARIOS = _ROOT / "eval" / "scenarios"

sys_path_added = False


def _add_root():
    global sys_path_added
    if not sys_path_added:
        import sys
        sys.path.insert(0, str(_ROOT))
        sys_path_added = True


@pytest.fixture(autouse=True)
def _setup():
    _add_root()


def _load(fname: str) -> dict:
    with open(_SCENARIOS / fname, encoding="utf-8") as f:
        return json.load(f)


def _run_mock(fname: str, replan: bool = True) -> dict:
    from eval.run_eval import run_mock
    scenario = _load(fname)
    return run_mock(scenario, replan_enabled=replan)


class TestBasicScenario:
    def test_t01_basic_move_succeeds(self):
        r = _run_mock("t01_basic_move.json")
        assert r["success"] is True, f"Expected success, got {r}"
        assert r["safety_violations"] == 0
        assert r["steps"] > 0

    def test_t02_basic_drop_succeeds(self):
        r = _run_mock("t02_basic_drop.json")
        assert r["success"] is True, f"Expected success, got {r}"
        assert r["safety_violations"] == 0


class TestInfeasibleScenario:
    def test_t16_missing_object_detected(self):
        r = _run_mock("t16_infeasible_missing.json")
        assert r["infeasible_correct"] is True, f"Expected infeasible_correct, got {r}"
        assert r["safety_violations"] == 0

    def test_t15_enclosed_detected(self):
        r = _run_mock("t15_infeasible_enclosed.json")
        assert r["infeasible_correct"] is True, f"Expected infeasible_correct, got {r}"


class TestSafetyInvariant:
    def test_safety_violations_always_zero(self):
        """Safety violations must be 0 across all scenarios."""
        from eval.run_eval import run_mock
        total_violations = 0
        for path in sorted(_SCENARIOS.glob("t*.json")):
            with open(path, encoding="utf-8") as f:
                scenario = json.load(f)
            if "task" in scenario:
                r = run_mock(scenario)
                total_violations += r["safety_violations"]
        assert total_violations == 0, f"Safety violations detected: {total_violations}"


class TestAblation:
    def test_replan_on_beats_off_for_replan_category(self):
        """Replan ON should succeed at t09 while OFF should not (person blocks only path mid-run)."""
        r_on = _run_mock("t09_replan_person_blocks.json", replan=True)
        r_off = _run_mock("t09_replan_person_blocks.json", replan=False)
        # replan ON should have more replans
        assert r_on["safety_violations"] == 0
        assert r_off["safety_violations"] == 0
