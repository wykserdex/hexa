"""Пример плагина HEXA Lab: «Отход» (rally).

Демонстрирует контракт из hexa/lab/plugins.py:
- класс-наследник LabModule, определённый в этом файле;
- только намерения (Intent) — прямого доступа к адаптеру и вводу нет;
- настройки живут в конфиге полигона и переживают перезапуск.

Запуск: python -m hexa lab --plugins-dir examples/plugins
Модуль появится на странице «Модули» (по умолчанию выключен).
"""
from __future__ import annotations

from hexa.lab.models import Intent, Kind, Point, WorldView
from hexa.lab.modules import LabModule


def _num(settings: dict, key: str, default: float, low: float, high: float) -> float:
    """Число из настроек с запасным значением: плагин не доверяет содержимому конфига."""
    try:
        value = float(settings.get(key, default))
    except (TypeError, ValueError):
        return default
    if value != value:  # NaN
        return default
    return min(high, max(low, value))


class Rally(LabModule):
    key, title = "rally", "Отход к точке сбора"
    description = "При низком здоровье уводит героя к точке сбора"
    # Выше фарма (10) и микро (20), ниже комбо (60), автопредметов (90) и игрока (100).
    priority = 30
    requires = frozenset({Kind.MOVE})

    def __init__(self) -> None:
        super().__init__(enabled=False, settings={"threshold": 35, "x": 120, "y": 480})

    def plan(self, world: WorldView, selected: str) -> list[Intent]:
        if not self.ready(world.time, .8):
            return []
        hero = world.hero
        threshold = _num(self.settings, "threshold", 35, 5, 90) / 100
        if not hero.alive or hero.hp_fraction > threshold:
            return []
        point = Point(_num(self.settings, "x", 120, 20, 980), _num(self.settings, "y", 480, 20, 580))
        if hero.position.distance(point) < 15:
            return []
        return [Intent(self.key, hero.id, Kind.MOVE, self.priority, world.time,
                       world.time + .8, point=point)]
