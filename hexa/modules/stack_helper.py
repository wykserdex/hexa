"""Модуль: окно стака нейтралов.

Считает по игровым часам, а не по реакции: нейтральные лагеря спавнятся на каждой
полной минуте, значит окно стака — за несколько секунд до неё. Модуль просто
напоминает, что окно открылось; решение остаётся за игроком.
"""
from __future__ import annotations

from hexa.module import Module
from hexa.timers import STACK_SCHEDULE, fmt_time


class StackHelper(Module):
    key = "stack_helper"
    title = "Окно стака"
    desc = "Напоминание за N секунд до спавна нейтралов (по умолчанию 15)"

    def on_tick(self, now: float) -> None:
        assert self.rt is not None
        lead = float(self.settings.get("lead_seconds", 15))
        for schedule, at in self.rt.engine.due_soon(lead, {"stack": STACK_SCHEDULE}, ["stack"]):
            if not self.rt.engine.mark_notified(schedule.key, at):
                continue
            self.rt.notify(
                title=f"Окно стака: {int(at - now)} с",
                text=f"спавн нейтралов в {fmt_time(at)}",
                kind="timer",
                source=self.key,
            )
