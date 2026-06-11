"""Quick smoke test: chạy agent 1 task (m01_basic_a) với timeout 600s."""
import asyncio
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from src.services.world import World, set_current_world  # noqa: E402
from src.agents.graph import build_graph  # noqa: E402

scen = json.loads((_ROOT / "eval/scenarios/m01_basic_a.json").read_text(encoding="utf-8"))
world = World.from_scenario(scen)
set_current_world(world)
task = scen["task"]
print(f"Goal: {task['goal_text']}", flush=True)


async def run():
    t0 = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            build_graph().ainvoke(
                {"goal_text": task["goal_text"], "history": [], "steps": 0, "replans": 0},
                config={"recursion_limit": 200},
            ),
            timeout=600.0,
        )
        elapsed = time.perf_counter() - t0
        status = result.get("status")
        steps = result.get("steps")
        hist = result.get("history") or []
        print(f"STATUS: {status}  steps={steps}  elapsed={elapsed:.1f}s", flush=True)
        print(f"HISTORY_LEN: {len(hist)}", flush=True)
        if hist:
            print(f"FIRST_STEP: {hist[0]}", flush=True)
    except Exception as e:
        elapsed = time.perf_counter() - t0
        print(f"ERROR after {elapsed:.1f}s: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()


asyncio.run(run())
