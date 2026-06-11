from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Cell(BaseModel):
    x: int
    y: int


class Entity(BaseModel):
    id: str
    kind: Literal["robot", "object", "person", "obstacle"]
    label: str | None = None
    pos: Cell
    carrying: str | None = None


class Zone(BaseModel):
    name: str
    cells: list[Cell]


class WorldState(BaseModel):
    width: int
    height: int
    robot: Entity
    objects: list[Entity]
    people: list[Entity]
    obstacles: list[Entity]
    zones: list[Zone]
    tick: int
    task: dict | None = None


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    goal_text: str


class RunResponse(BaseModel):
    plan: list[str]
    history: list[dict]
    answer: str
    status: str
