"""A deterministic local arena. NOT a Dota adapter; numbers are demonstration values."""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from types import MappingProxyType

from .models import Capabilities, Command, Kind, Point, Result, SkillView, UnitView, WorldView


SKILLS = (
    SkillView("tornado", "Вихрь", 70, 8, 0, 510, 65, .18),
    SkillView("emp", "Импульс", 95, 10, 0, 510, 90, .18),
    SkillView("meteor", "Метеор", 110, 12, 0, 510, 145, .28),
    SkillView("blast", "Волна", 80, 9, 0, 510, 85, .18),
)
ITEM = SkillView("restore", "Восстановление", 0, 14, 0, 0)


@dataclass
class Unit:
    id: str
    name: str
    team: str
    role: str
    position: Point
    hp: float
    max_hp: float
    mana: float = 0
    max_mana: float = 0
    controllable: bool = False
    attack_range: float = 88
    attack_ready_at: float = 0
    speed: float = 110
    damage: float = 38
    goal: Point | None = None
    order_source: str = ""
    respawn_at: float | None = None
    home: Point | None = None

    def view(self) -> UnitView:
        return UnitView(self.id, self.name, self.team, self.role, self.position,
                        self.hp, self.max_hp, self.mana, self.max_mana,
                        self.controllable, self.attack_range, self.attack_ready_at,
                        self.order_source)


class Simulator:
    capabilities = Capabilities("Local Arena", "simulator")

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.time = 0.0
        self.units = {
            "hero": Unit("hero", "Арканист", "ally", "hero", Point(260, 350), 1000, 1000,
                         650, 650, True, damage=52),
            "ally-1": Unit("ally-1", "Искра I", "ally", "summon", Point(210, 430),
                           360, 360, controllable=True, speed=140, damage=27),
            "ally-2": Unit("ally-2", "Искра II", "ally", "summon", Point(185, 340),
                           360, 360, controllable=True, speed=140, damage=27),
            "enemy-1": Unit("enemy-1", "Страж", "enemy", "hero", Point(645, 230), 1600, 1600),
            "enemy-2": Unit("enemy-2", "Разведчик", "enemy", "hero", Point(750, 340), 1200, 1200),
            "creep-1": Unit("creep-1", "Нейтрал I", "neutral", "creep", Point(425, 420), 260, 260),
            "creep-2": Unit("creep-2", "Нейтрал II", "neutral", "creep", Point(485, 450), 300, 300),
            "creep-3": Unit("creep-3", "Нейтрал III", "neutral", "creep", Point(455, 505), 220, 220),
        }
        for unit in self.units.values():
            unit.home = unit.position
        self.skills = {s.key: s for s in SKILLS}
        self.items = {ITEM.key: ITEM}
        self.effects: list[dict] = []
        self.effect_seq = 0
        self.kills = 0
        self.gold = 0

    def observe(self) -> WorldView:
        return WorldView(self.time, "hero",
                         MappingProxyType({k: v.view() for k, v in self.units.items()}),
                         MappingProxyType(dict(self.skills)), MappingProxyType(dict(self.items)))

    def effect(self, kind: str, start: Point, end: Point, text: str = "") -> None:
        self.effect_seq += 1
        self.effects.append({"id": self.effect_seq, "kind": kind, "from": start.json(),
                             "to": end.json(), "time": self.time, "text": text})
        self.effects = self.effects[-40:]

    def _damage(self, unit: Unit, amount: float) -> None:
        unit.hp = max(0, unit.hp - amount)
        if unit.hp == 0:
            unit.goal = None
            unit.respawn_at = self.time + (8 if unit.team == "neutral" else 12)
            self.kills += 1
            self.gold += 35 if unit.team == "neutral" else 150

    def advance(self, seconds: float) -> None:
        self.time += seconds
        for unit in self.units.values():
            if unit.hp <= 0:
                if unit.respawn_at is not None and self.time >= unit.respawn_at:
                    unit.hp = unit.max_hp
                    unit.position = unit.home or unit.position
                    unit.respawn_at = None
                    unit.order_source = ""
                    self.effect("spawn", unit.position, unit.position)
                continue
            if unit.controllable:
                unit.hp = min(unit.max_hp, unit.hp + 1.8 * seconds)
                unit.mana = min(unit.max_mana, unit.mana + 8 * seconds)
            if unit.goal:
                distance = unit.position.distance(unit.goal)
                step = unit.speed * seconds
                if distance <= step:
                    unit.position = unit.goal
                    unit.goal = None
                elif distance:
                    unit.position = Point(unit.position.x + (unit.goal.x - unit.position.x) * step / distance,
                                          unit.position.y + (unit.goal.y - unit.position.y) * step / distance)
        self.effects = [e for e in self.effects if self.time - e["time"] < 2]

    def stop_orders(self, source: str | None = None) -> None:
        for unit in self.units.values():
            if unit.controllable and (source is None or unit.order_source == source):
                unit.goal = None
                unit.order_source = ""

    def execute(self, command: Command) -> Result:
        i = command.intent
        actor = self.units.get(i.actor)
        if not actor or not actor.controllable:
            return Result(False, "Юнит недоступен для управления")
        if actor.hp <= 0:
            return Result(False, "Исполнитель погиб")
        if i.kind not in self.capabilities.actions:
            return Result(False, "Адаптер не поддерживает действие")

        if i.kind == Kind.STOP:
            actor.goal = None
            actor.order_source = ""
            return Result(True, "Приказ остановки исполнен")

        if i.kind == Kind.MOVE:
            p = i.point
            if not p or not all(isfinite(v) for v in (p.x, p.y)) or not (20 <= p.x <= 980 and 20 <= p.y <= 580):
                return Result(False, "Координаты вне полигона")
            actor.goal = p
            actor.order_source = i.source
            return Result(True, "Приказ движения применён")

        if i.kind == Kind.ITEM:
            skill = self.items.get(i.ability)
            if actor.id != "hero" or skill is None:
                return Result(False, "Предмет недоступен")
            if self.time + 1e-8 < skill.ready_at:
                return Result(False, "Предмет на перезарядке")
            before = actor.hp
            actor.hp = min(actor.max_hp, actor.hp + 420)
            self.items[skill.key] = replace(skill, ready_at=self.time + skill.cooldown)
            self.effect("heal", actor.position, actor.position, f"+{round(actor.hp - before)} HP")
            return Result(True, f"Восстановлено {round(actor.hp - before)} HP")

        target = self.units.get(i.target)
        if not target or target.hp <= 0:
            return Result(False, "Цель недоступна или погибла")
        if target.team == actor.team:
            return Result(False, "Нельзя атаковать союзника")
        distance = actor.position.distance(target.position)

        if i.kind == Kind.CAST:
            skill = self.skills.get(i.ability)
            if actor.id != "hero" or skill is None:
                return Result(False, "Способность недоступна")
            if distance > skill.range:
                return Result(False, "Цель вне дальности способности")
            if self.time + 1e-8 < skill.ready_at:
                return Result(False, "Способность на перезарядке")
            if actor.mana < skill.mana:
                return Result(False, "Недостаточно маны")
            actor.goal = None
            actor.order_source = i.source
            actor.mana -= skill.mana
            self.skills[skill.key] = replace(skill, ready_at=self.time + skill.cooldown)
            self._damage(target, skill.damage)
            self.effect(skill.key, actor.position, target.position, f"−{int(skill.damage)}")
            return Result(True, f"{skill.title}: {int(skill.damage)} урона", skill.cast_time)

        if i.kind == Kind.ATTACK:
            if distance > actor.attack_range + 2:
                return Result(False, "Цель вне дальности атаки")
            if self.time + 1e-8 < actor.attack_ready_at:
                return Result(False, "Атака ещё не готова")
            actor.goal = None
            actor.order_source = i.source
            actor.attack_ready_at = self.time + .85
            self._damage(target, actor.damage)
            self.effect("attack", actor.position, target.position, f"−{int(actor.damage)}")
            return Result(True, f"Атака: {int(actor.damage)} урона", .15)

        return Result(False, "Неизвестный вид команды")

    def damage_hero(self) -> None:
        hero = self.units["hero"]
        before = hero.hp
        hero.hp = min(hero.hp, hero.max_hp * .28)
        self.effect("damage", hero.position, hero.position, f"−{int(before - hero.hp)} HP")

    def presentation(self) -> dict:
        return {"effects": list(self.effects), "gold": self.gold, "kills": self.kills,
                "size": {"width": 1000, "height": 600}}
