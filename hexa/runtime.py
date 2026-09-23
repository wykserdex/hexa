"""Runtime — то, что получает модуль: конфиг, часы, шина, уведомления, sink действий."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

from hexa.bus import Event, EventBus
from hexa.config import Config
from hexa.timers import TimerEngine, fmt_time


@dataclass
class Notification:
    t: float
    title: str
    text: str = ""
    kind: str = "info"      # info | timer | warn | action
    source: str = ""

    def line(self) -> str:
        tail = f" — {self.text}" if self.text else ""
        return f"[{fmt_time(self.t)}] {self.title}{tail}"

    def kind_icon(self) -> str:
        return {"timer": "◷", "warn": "!", "action": "➜", "info": "·"}.get(self.kind, "·")


@dataclass
class Runtime:
    config: Config
    bus: EventBus = field(default_factory=EventBus)
    engine: TimerEngine = field(default_factory=TimerEngine)
    sink: Any = None
    notifications: deque[Notification] = field(default_factory=lambda: deque(maxlen=60))
    verbose: bool = False
    _hotkeys: dict[str, list[Callable[[], None]]] = field(default_factory=dict)

    # ------------------------------------------------------------ доступ

    @property
    def now(self) -> float:
        return self.engine.now

    @property
    def sandbox(self) -> bool:
        """Автоматизация разрешена только здесь: боты, своё лобби, кастомка."""
        return self.config.sandbox

    # ------------------------------------------------------------ уведомления

    def notify(self, title: str, text: str = "", kind: str = "info", source: str = "") -> Notification:
        note = Notification(t=self.now, title=title, text=text, kind=kind, source=source)
        self.notifications.append(note)
        self.bus.publish(Event("notify", {"note": note}, t=self.now))
        if self.verbose:
            print(f"  {note.kind_icon()} {note.line()}")
        return note

    # ------------------------------------------------------------ действия в игру

    def actions(self, *items: str) -> None:
        """Отправить намерения в sink. В обычном режиме sink — только трейс."""
        if self.sink is None:
            return
        self.sink.push(list(items), t=self.now)

    # ------------------------------------------------------------ хоткеи

    def bind_hotkey(self, action: str, handler: Callable[[], None]) -> None:
        self._hotkeys.setdefault(action, []).append(handler)

    def unbind_hotkey(self, action: str, handler: Callable[[], None]) -> None:
        handlers = self._hotkeys.get(action, [])
        if handler in handlers:
            handlers.remove(handler)

    def press(self, action: str) -> None:
        """Нажатие хоткея: он же используется в демо-прогоне, чтобы всё было проверяемо."""
        for handler in list(self._hotkeys.get(action, [])):
            try:
                handler()
            except Exception as exc:  # noqa: BLE001
                self.notify(f"Сбой обработчика {action}", str(exc), "warn")

    def hotkey_rows(self) -> list[tuple[str, str]]:
        return [(action, str(self.config.get("hotkeys", action, default="—"))) for action in self._hotkeys]
