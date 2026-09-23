"""Модуль: тайминги рун. Данные — официальный GSI, физику знает движок таймеров."""
from __future__ import annotations

from hexa.module import Module
from hexa.timers import RUNE_SCHEDULES, fmt_time


class RuneAlerts(Module):
    key = "rune_alerts"
    title = "Тайминги рун"
    desc = "Баунти, вотер, павер, лотус, виздом — с предупреждением заранее"

    def on_tick(self, now: float) -> None:
        assert self.rt is not None
        horizon = float(self.rt.config.get("general", "notify_seconds_before", default=20))
        wanted = [k for k, enabled in self.settings.items() if enabled and k in RUNE_SCHEDULES]
        if not wanted:
            return

        for schedule, at in self.rt.engine.due_soon(horizon, RUNE_SCHEDULES, wanted):
            if not self.rt.engine.mark_notified(schedule.key, at):
                continue
            left = at - now
            self.rt.notify(
                title=f"{schedule.title} через {int(left)} с",
                text=f"появление в {fmt_time(at)}",
                kind="timer",
                source=self.key,
            )
