"""Шина событий: модули общаются через неё, а не друг через друга."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Event:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    t: float = 0.0


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.topic, []):
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - сбой подписчика не рвёт остальных
                continue
