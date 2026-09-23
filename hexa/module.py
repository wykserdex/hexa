"""Контракт модуля обвязки.

Модуль видит: состояние GSI, игровое время, конфиг, шину и sink действий.
Модуль не видит: память игры, окна, ввод. Поэтому модуль не может «сжульничать» —
у него физически нет инструментов шире, чем разрешает носитель.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # чтобы не ловить циклы импортов
    from hexa.runtime import Runtime


class Module(ABC):
    key: str = "unnamed"
    title: str = "Без названия"
    desc: str = ""
    default_on: bool = False

    def __init__(self) -> None:
        self.enabled = False
        self.rt: "Runtime | None" = None
        self.settings: dict[str, Any] = {}

    # ------------------------------------------------------------ жизненный цикл

    def bind(self, runtime: "Runtime") -> None:
        self.rt = runtime
        self.settings = runtime.config.module(self.key)

    def enable(self) -> None:
        if not self.enabled:
            self.enabled = True
            self.on_enable()

    def disable(self) -> None:
        if self.enabled:
            self.enabled = False
            self.on_disable()

    def on_enable(self) -> None:
        """Подписки на хоткеи и шину удобно делать здесь, а снимать — в on_disable."""

    def on_disable(self) -> None:
        """Снять подписки, погасить внутренние таймеры."""

    # ------------------------------------------------------------ события

    def on_state(self, state: Any) -> None:
        """Пришёл свежий снимок GSI (только то, что Valve отдаёт игроку)."""

    def on_tick(self, now: float) -> None:
        """Игровое время продвинулось."""

    def on_hotkey(self, action: str) -> None:
        """Нажато действие, привязанное к этому модулю."""

    # ------------------------------------------------------------ служебное

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value
        if self.rt:
            self.rt.config.save()
