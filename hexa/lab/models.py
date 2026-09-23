"""Typed, immutable observations and structured commands shared by modules/adapters."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from math import hypot
from typing import Mapping, Protocol


class Priority(IntEnum):
    FARM = 10
    MICRO = 20
    COMBO = 60
    SURVIVAL = 90
    MANUAL = 100


class Kind(str, Enum):
    CAST = "cast"
    ITEM = "item"
    ATTACK = "attack"
    MOVE = "move"
    STOP = "stop"


class Status(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def distance(self, other: Point) -> float:
        return hypot(self.x - other.x, self.y - other.y)

    def json(self) -> dict:
        return {"x": round(self.x, 2), "y": round(self.y, 2)}


@dataclass(frozen=True)
class UnitView:
    id: str
    name: str
    team: str
    role: str
    position: Point
    hp: float
    max_hp: float
    mana: float
    max_mana: float
    controllable: bool
    attack_range: float
    attack_ready_at: float
    order_source: str = ""

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def hp_fraction(self) -> float:
        return self.hp / self.max_hp


@dataclass(frozen=True)
class SkillView:
    key: str
    title: str
    mana: float
    cooldown: float
    ready_at: float
    range: float
    damage: float = 0
    cast_time: float = 0


@dataclass(frozen=True)
class WorldView:
    time: float
    player_id: str
    units: Mapping[str, UnitView]
    skills: Mapping[str, SkillView]
    items: Mapping[str, SkillView]

    @property
    def hero(self) -> UnitView:
        return self.units[self.player_id]


@dataclass(frozen=True)
class Intent:
    source: str
    actor: str
    kind: Kind
    priority: int
    due: float
    expires: float
    ability: str = ""
    target: str = ""
    point: Point | None = None
    group: str = ""


@dataclass
class Command:
    id: int
    intent: Intent
    created: float
    status: Status = Status.PENDING
    reason: str = "В очереди"
    finished: float | None = None

    def json(self) -> dict:
        i = self.intent
        return {
            "id": self.id, "source": i.source, "actor": i.actor,
            "kind": i.kind.value, "priority": int(i.priority),
            "due": round(i.due, 3), "expires": round(i.expires, 3),
            "ability": i.ability, "target": i.target,
            "point": i.point.json() if i.point else None, "group": i.group,
            "created": round(self.created, 3), "status": self.status.value,
            "reason": self.reason,
            "finished": round(self.finished, 3) if self.finished is not None else None,
        }


@dataclass(frozen=True)
class Result:
    ok: bool
    reason: str
    busy_for: float = 0


@dataclass(frozen=True)
class Capabilities:
    name: str
    mode: str
    actions: frozenset[Kind] = field(default_factory=lambda: frozenset(Kind))
    multi_unit: bool = True
    connected_to_dota: bool = False


class GameAdapter(Protocol):
    """An adapter owns game state; modules can observe it but cannot mutate it.

    execute() in this synchronous prototype returns the SIMULATOR's acknowledgement.
    A real, asynchronous adapter must introduce accepted/confirmed/timeout states;
    handing a command to a transport must never count as executed.
    """
    capabilities: Capabilities

    def observe(self) -> WorldView: ...
    def execute(self, command: Command) -> Result: ...
    def advance(self, seconds: float) -> None: ...
    def stop_orders(self, source: str | None = None) -> None: ...
    def reset(self) -> None: ...
    def presentation(self) -> dict: ...
