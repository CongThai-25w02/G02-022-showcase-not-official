from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.config import get_settings


def _configure_langsmith() -> None:
    """Enable LangSmith tracing if env vars are present (no-op otherwise)."""
    if os.getenv("LANGCHAIN_API_KEY") and not os.getenv("LANGCHAIN_TRACING_V2"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "ai20k-162-task-planner")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_langsmith()
    settings = get_settings()
    print(f"Starting {settings.app_name} in {settings.app_env} mode")
    yield
    print("Shutting down...")


app = FastAPI(
    title="AI20K-162 Task Planner",
    description="Robot warehouse task planning agent (sim 2D)",
    version="0.2.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


# Serve frontend static files — must be mounted last so API routes take priority.
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
