"""Хоткеи: объявленные действия, биндинги, проверка конфликтов.

Хоткей здесь — это действие обвязки (открыть меню, отметить таймер, запустить комбо).
Он не эмулирует твои игровые кнопки: макросов, повторяющих ввод, тут нет и не будет.
"""
from __future__ import annotations

from dataclasses import dataclass

from hexa.config import Config

# Действие -> человеческое описание. Всё, что обвязка умеет по кнопке.
ACTIONS: dict[str, str] = {
    "menu": "Открыть меню обвязки",
    "toggle_mode": "Включить / выключить модули разом",
    "mark_timer": "Отметить таймер (поставил — считаем)",
    "combo": "Комбо: только в песочнице (боты / своё лобби / кастомка)",
}


@dataclass
class Binding:
    action: str
    key: str
    description: str


class HotkeyRegistry:
    def __init__(self, config: Config) -> None:
        self.config = config

    def key_for(self, action: str) -> str:
        return str(self.config.get("hotkeys", action, default=""))

    def bindings(self) -> list[Binding]:
        return [
            Binding(action=action, key=self.key_for(action), description=desc)
            for action, desc in ACTIONS.items()
        ]

    def conflicts(self) -> list[tuple[str, str, str]]:
        """(клавиша, действие1, действие2) — чтобы меню не выглядело как сломанное."""
        seen: dict[str, str] = {}
        found: list[tuple[str, str, str]] = []
        for binding in self.bindings():
            if not binding.key:
                continue
            other = seen.get(binding.key)
            if other and other != binding.action:
                found.append((binding.key, other, binding.action))
            seen[binding.key] = binding.action
        return found

    def rows(self) -> list[tuple[str, str, str]]:
        return [(b.key or "—", b.action, b.description) for b in self.bindings()]
