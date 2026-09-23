"""Движок таймеров: расписания рун, стаков и ручные отметки.

Расписания — параметры патча. Лежат в одном месте, чтобы после обновления игры
их можно было поправить строкой, а не лазить по модулям.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def fmt_time(t: float) -> str:
    sign = "-" if t < 0 else ""
    t = abs(t)
    return f"{sign}{int(t // 60)}:{int(t % 60):02d}"


@dataclass(frozen=True)
class Schedule:
    """Расписание события: либо явные времена, либо первый раз + интервал."""

    key: str
    title: str
    first: float = 0.0
    interval: float = 0.0
    times: tuple[float, ...] = ()

    def occurrences(self, start: float, end: float) -> list[float]:
        if end <= start:
            return []
        found: list[float] = []
        for t in self.times:
            if start < t <= end:
                found.append(t)
        if self.interval > 0:
            n = 0
            t = self.first
            if t <= start:
                import math

                n = int(math.floor((start - t) / self.interval)) + 1
                t = self.first + n * self.interval
            while t <= end:
                found.append(t)
                t += self.interval
        return sorted(found)


# Дефолтные расписания. Перед релизом сверяй с текущим патчем — они меняются.
RUNE_SCHEDULES: dict[str, Schedule] = {
    "bounty": Schedule("bounty", "Баунти-руна", first=0.0, interval=180.0),
    "water": Schedule("water", "Вотер-руна", times=(120.0, 240.0)),
    "power": Schedule("power", "Павер-руна", first=360.0, interval=120.0),
    "lotus": Schedule("lotus", "Лотус", first=180.0, interval=180.0),
    "wisdom": Schedule("wisdom", "Виздом-руна", first=420.0, interval=420.0),
}
STACK_SCHEDULE = Schedule("stack", "Стак нейтралов", first=60.0, interval=60.0)


@dataclass
class ManualTimer:
    label: str
    created: float
    due: float
    fired: bool = False


@dataclass
class TimerEngine:
    """Хранит игровое время, считает предстоящие события и ручные таймеры."""

    now: float = 0.0
    started: bool = False
    manual: list[ManualTimer] = field(default_factory=list)
    _notified: set[tuple[str, float]] = field(default_factory=set)

    # ------------------------------------------------------------ время

    def sync(self, now: float) -> None:
        """Передаём текущее игровое время. Откат назад = новая игра."""
        if self.started and now < self.now:
            self.reset(now)
            return
        self.started = True
        self.now = now

    def reset(self, now: float = 0.0) -> None:
        self.now = now
        self.started = True
        self.manual.clear()
        self._notified.clear()

    # ------------------------------------------------------------ события

    def due_soon(
        self, horizon: float, schedules: dict[str, Schedule] | None = None, keys: list[str] | None = None
    ) -> list[tuple[Schedule, float]]:
        schedules = schedules or RUNE_SCHEDULES
        wanted = keys or list(schedules)
        result: list[tuple[Schedule, float]] = []
        for key in wanted:
            schedule = schedules.get(key)
            if schedule is None:
                continue
            for t in schedule.occurrences(self.now, self.now + horizon):
                result.append((schedule, t))
        return sorted(result, key=lambda item: item[1])

    def mark_notified(self, key: str, t: float) -> bool:
        """True — если про это событие ещё не говорили (защита от спама)."""
        fingerprint = (key, round(t, 1))
        if fingerprint in self._notified:
            return False
        self._notified.add(fingerprint)
        return True

    # ------------------------------------------------------------ ручные таймеры

    def add_manual(self, label: str, lifetime_s: float) -> ManualTimer:
        timer = ManualTimer(label=label, created=self.now, due=self.now + lifetime_s)
        self.manual.append(timer)
        return timer

    def collect_expired(self) -> list[ManualTimer]:
        expired = [m for m in self.manual if not m.fired and m.due <= self.now]
        for timer in expired:
            timer.fired = True
        self.manual = [m for m in self.manual if not m.fired]
        return expired

    def manual_rows(self) -> list[tuple[str, str, str]]:
        return [
            (m.label, fmt_time(m.created), f"осталось {max(0, int(m.due - self.now))} с")
            for m in sorted(self.manual, key=lambda m: m.due)
        ]

    def upcoming_rows(self, horizon: float = 90.0) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for schedule, t in self.due_soon(horizon):
            rows.append((schedule.title, fmt_time(t), f"через {int(t - self.now)} с"))
        return rows
