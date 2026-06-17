from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from src.agents.graph import agent
from src.api.scenario_catalog import EVAL_QUICK, list_scenarios
from src.models.schemas import RunRequest, RunResponse, WorldState
from src.services.world import World, get_current_world, set_current_world

router = APIRouter()

_SCENARIO_DIR = Path(__file__).parent.parent.parent / "eval" / "scenarios"


# ---------------------------------------------------------------------------
# World endpoints (Phase 0)
# ---------------------------------------------------------------------------


@router.get("/world", response_model=WorldState)
async def get_world_state() -> WorldState:
    return get_current_world().to_state()


@router.post("/world", response_model=WorldState)
async def set_world_state(state: WorldState) -> WorldState:
    """Set the current world from a user-built scene (e.g. the 3D editor) so the
    agent reasons on it. Invariants are not enforced here — the user is free to
    arrange entities however they like."""
    world = World.from_scenario(state.model_dump(), check_invariants=False)
    set_current_world(world)
    return world.to_state()


@router.get("/scenarios")
async def get_scenarios() -> dict:
    """List all eval/demo scenarios for the web UI dropdown."""
    return {"scenarios": list_scenarios(), "eval_quick": EVAL_QUICK}


@router.post("/scenario", response_model=WorldState)
async def load_scenario(name: str) -> WorldState:
    path = _SCENARIO_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    world = World.from_scenario(path)
    set_current_world(world)
    return world.to_state()


# ---------------------------------------------------------------------------
# Agent run endpoint (Phase 2)
# ---------------------------------------------------------------------------


@router.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest) -> RunResponse:
    """Run the task-planning agent end-to-end and return the full trace."""
    result = await agent.ainvoke({"goal_text": request.goal_text})
    return RunResponse(
        plan=result.get("plan") or [],
        history=result.get("history") or [],
        answer=result.get("answer") or "",
        status=result.get("status") or "unknown",
    )


# ---------------------------------------------------------------------------
# WebSocket streaming (Phase 2)
# ---------------------------------------------------------------------------


@router.websocket("/ws")
async def ws_agent(websocket: WebSocket) -> None:
    """Stream agent steps in real-time.

    Client sends JSON: {"goal_text": "..."}
    Server streams JSON events: {"type": "step"|"world"|"done"|"error", ...}
    """
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        payload = json.loads(data)
        goal_text: str = payload.get("goal_text", "")

        async for event in agent.astream({"goal_text": goal_text}):
            for node_name, node_state in event.items():
                msg: dict = {"type": "step", "node": node_name}
                if "history" in node_state and node_state["history"]:
                    msg["last_action"] = node_state["history"][-1]
                if "world_view" in node_state:
                    msg["world_view"] = node_state["world_view"]
                if "status" in node_state:
                    msg["status"] = node_state["status"]
                if "plan" in node_state:
                    msg["plan"] = node_state["plan"]
                if "answer" in node_state:
                    msg["answer"] = node_state["answer"]
                if "pending_question" in node_state:
                    msg["pending_question"] = node_state["pending_question"]
                # Always include a compact world snapshot for frontend animation
                msg["world"] = get_current_world().to_snapshot()
                await websocket.send_text(json.dumps(msg, ensure_ascii=False))

        await websocket.send_text(json.dumps({"type": "done"}, ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError as exc:
        await websocket.send_text(json.dumps({"type": "error", "detail": str(exc)}))
