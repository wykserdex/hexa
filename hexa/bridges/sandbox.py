"""Мост действий: сюда прилетает всё, что модули хотят сделать в игре.

Два режима:
  SandboxTraceSink — только трейс, в игру не влияет (по умолчанию).
  GuardedSink      — трейс + очередь в мост; пропускает действия ТОЛЬКО если рантайм
                     находится в песочнице. Это и есть предохранитель: даже если модуль
                     ошибётся и захочет что-то нажать в ranked, действие не пройдёт дальше
                     этого класса.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ActionRecord:
    t: float
    items: list[str]


class SandboxTraceSink:
    """Sink по умолчанию: пишет трейс, в игру не влияет."""

    name = "trace"

    def __init__(self) -> None:
        self.records: list[ActionRecord] = []

    def push(self, items: list[str], t: float = 0.0) -> None:
        self.records.append(ActionRecord(t=t, items=list(items)))

    def dump(self) -> str:
        if not self.records:
            return "(действий не было)"
        return "\n".join(
            f"[{record.t:6.2f}s] " + "; ".join(record.items) for record in self.records
        )


@dataclass
class GuardedSink:
    """TraceSink + очередь в игровой мост, с проверкой песочницы на каждом действии."""

    sandbox: Callable[[], bool] = lambda: False
    queue: Any = None
    name = "bridge"
    records: list[ActionRecord] = field(default_factory=list)
    rejected: int = 0

    def push(self, items: list[str], t: float = 0.0) -> None:
        self.records.append(ActionRecord(t=t, items=list(items)))
        if not self.sandbox():
            self.rejected += 1
            return
        if self.queue is not None:
            self.queue.put(list(items), t)

    def dump(self) -> str:
        if not self.records:
            return "(действий не было)"
        lines = [f"[{r.t:6.2f}s] " + "; ".join(r.items) for r in self.records]
        if self.rejected:
            lines.append(f"отклонено вне песочницы: {self.rejected}")
        return "\n".join(lines)
