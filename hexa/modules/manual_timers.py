"""Модуль: ручные таймеры. Игрок сам жмёт кнопку — обвязка считает срок.

Пример из спеки: Течис. Ставишь мину, жмёшь хоткей — ассистент напоминает, когда
срок истекает или когда враг может пройти через это место. Тут нет автоматической
постановки или детонации: действие инициирует человек, и это принципиально.
"""
from __future__ import annotations

from hexa.module import Module
from hexa.timers import fmt_time


class ManualTimers(Module):
    key = "manual_timers"
    title = "Ручные отметки"
    desc = "Нажал хоткей — считаем срок и напомним (мины, варды, кулдауны врагов)"

    def on_enable(self) -> None:
        assert self.rt is not None
        self.rt.bind_hotkey("mark_timer", self._mark)

    def on_disable(self) -> None:
        assert self.rt is not None
        self.rt.unbind_hotkey("mark_timer", self._mark)

    # ------------------------------------------------------------ логика

    def _mark(self) -> None:
        assert self.rt is not None
        lifetime = float(self.settings.get("default_lifetime_s", 180))
        label = str(self.settings.get("label", "мина"))
        timer = self.rt.engine.add_manual(label, lifetime)
        self.rt.notify(
            title=f"Отметка: {label}",
            text=f"напомню в {fmt_time(timer.due)}",
            kind="action",
            source=self.key,
        )

    def on_tick(self, now: float) -> None:
        assert self.rt is not None
        for timer in self.rt.engine.collect_expired():
            self.rt.notify(
                title=f"{timer.label}: срок истёк",
                text=f"поставлено в {fmt_time(timer.created)}",
                kind="timer",
                source=self.key,
            )
