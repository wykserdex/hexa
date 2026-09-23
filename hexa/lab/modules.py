"""Modules only produce intentions. No module can call an adapter directly."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import ClassVar

from .models import Intent, Kind, Point, Priority, WorldView


@dataclass
class LabModule:
    enabled: bool = True
    settings: dict = field(default_factory=dict)
    _next: float = 0
    key: ClassVar[str] = "base"
    title: ClassVar[str] = "Module"
    description: ClassVar[str] = ""
    origin: ClassVar[str] = "builtin"
    priority: ClassVar[int] = 0
    requires: ClassVar[frozenset[Kind]] = frozenset()

    def reset(self) -> None:
        self._next = 0

    def plan(self, world: WorldView, selected: str) -> list[Intent]:
        return []

    def ready(self, now: float, interval: float) -> bool:
        if now + 1e-8 < self._next:
            return False
        self._next = now + interval
        return True


class Combo(LabModule):
    key, title, priority = "combo", "Комбо", Priority.COMBO
    requires = frozenset({Kind.CAST})
    steps = ((0, "tornado"), (.60, "emp"), (1.25, "meteor"), (1.95, "blast"))

    def sequence(self, world: WorldView, selected: str, group: str) -> list[Intent]:
        hero = world.hero
        target = world.units.get(selected)
        if not target or not target.alive or target.team == "ally":
            raise ValueError("Выбери живую вражескую или нейтральную цель")
        if not hero.alive:
            raise ValueError("Герой недоступен")
        skills = [world.skills[name] for _, name in self.steps]
        if any(s.ready_at > world.time + 1e-8 for s in skills):
            raise ValueError("Дождись перезарядки всех четырёх способностей")
        if sum(s.mana for s in skills) > hero.mana:
            raise ValueError("Недостаточно маны для полной последовательности")
        if any(hero.position.distance(target.position) > s.range for s in skills):
            raise ValueError("Цель вне дальности комбо — выбери Стража или подойди ближе")
        return [Intent(self.key, hero.id, Kind.CAST, self.priority,
                       world.time + offset, world.time + offset + .55,
                       ability=name, target=target.id, group=group)
                for offset, name in self.steps]


class AutoItems(LabModule):
    key, title, priority = "guardian", "Автопредметы", Priority.SURVIVAL
    requires = frozenset({Kind.ITEM})

    def __init__(self) -> None:
        super().__init__(settings={"threshold": 40})

    def plan(self, world: WorldView, selected: str) -> list[Intent]:
        if not self.ready(world.time, .2):
            return []
        hero, item = world.hero, world.items["restore"]
        if hero.alive and hero.hp_fraction <= self.settings["threshold"] / 100 and item.ready_at <= world.time:
            return [Intent(self.key, hero.id, Kind.ITEM, self.priority, world.time,
                           world.time + .4, ability=item.key, target=hero.id)]
        return []


def approach(actor: Point, target: Point, stand_off: float) -> Point:
    dx, dy = actor.x - target.x, actor.y - target.y
    distance = hypot(dx, dy) or 1
    return Point(max(20, min(980, target.x + dx / distance * stand_off)),
                 max(20, min(580, target.y + dy / distance * stand_off)))


class Farm(LabModule):
    key, title, priority = "farm", "Фарм", Priority.FARM
    requires = frozenset({Kind.MOVE, Kind.ATTACK})

    def __init__(self) -> None:
        super().__init__(enabled=False)

    def plan(self, world: WorldView, selected: str) -> list[Intent]:
        if not self.ready(world.time, .65) or not world.hero.alive:
            return []
        hero = world.hero
        creeps = [u for u in world.units.values() if u.team == "neutral" and u.alive]
        if not creeps:
            return []
        target = min(creeps, key=lambda u: hero.position.distance(u.position))
        if hero.position.distance(target.position) > hero.attack_range:
            return [Intent(self.key, hero.id, Kind.MOVE, self.priority, world.time, world.time + .6,
                           point=approach(hero.position, target.position, hero.attack_range - 8), target=target.id)]
        if hero.attack_ready_at <= world.time:
            return [Intent(self.key, hero.id, Kind.ATTACK, self.priority, world.time, world.time + .5,
                           target=target.id)]
        return []


class Micro(LabModule):
    key, title, priority = "micro", "Микроконтроль", Priority.MICRO
    requires = frozenset({Kind.MOVE, Kind.ATTACK})

    def __init__(self) -> None:
        super().__init__(enabled=False)

    def plan(self, world: WorldView, selected: str) -> list[Intent]:
        if not self.ready(world.time, .9):
            return []
        enemies = [u for u in world.units.values() if u.team == "enemy" and u.alive]
        if not enemies:
            return []
        chosen = world.units.get(selected)
        result = []
        for unit in world.units.values():
            if not unit.controllable or unit.role != "summon" or not unit.alive:
                continue
            if unit.hp_fraction < .35:
                point = Point(max(30, world.hero.position.x - 65), min(565, world.hero.position.y + 45))
                if unit.position.distance(point) > 12:
                    result.append(Intent(self.key, unit.id, Kind.MOVE, self.priority, world.time,
                                         world.time + .8, point=point))
                continue
            target = chosen if chosen in enemies else min(enemies, key=lambda e: unit.position.distance(e.position))
            if unit.position.distance(target.position) > unit.attack_range:
                result.append(Intent(self.key, unit.id, Kind.MOVE, self.priority, world.time, world.time + .8,
                                     point=approach(unit.position, target.position, unit.attack_range - 8), target=target.id))
            elif unit.attack_ready_at <= world.time:
                result.append(Intent(self.key, unit.id, Kind.ATTACK, self.priority, world.time, world.time + .6,
                                     target=target.id))
        return result


def make_modules() -> dict[str, LabModule]:
    return {m.key: m for m in (Combo(), AutoItems(), Farm(), Micro())}
