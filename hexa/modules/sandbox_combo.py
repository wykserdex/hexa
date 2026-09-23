"""Модуль: комбо по хоткею. Работает только в песочнице.

Это и есть пункт 3 спеки: автоматизация существует, но живёт там, где это законно —
боты, своё лобби, кастомка. Вне песочницы модуль не «тихо отключается», а прямо говорит,
почему не может: так поведение предсказуемо и не превращается в сюрприз.
"""
from __future__ import annotations

from hexa.module import Module


class SandboxCombo(Module):
    key = "sandbox_combo"
    title = "Комбо (песочница)"
    desc = "Последовательность кастов по хоткею: только боты / своё лобби / кастомка"

    def on_enable(self) -> None:
        assert self.rt is not None
        self.rt.bind_hotkey("combo", self._run)

    def on_disable(self) -> None:
        assert self.rt is not None
        self.rt.unbind_hotkey("combo", self._run)

    def _run(self) -> None:
        assert self.rt is not None
        sequence = list(self.settings.get("sequence", []))
        offsets = list(self.settings.get("offsets", []))

        if not self.rt.sandbox:
            self.rt.notify(
                title="Комбо недоступно в обычном режиме",
                text="включи песочницу (бот-матч, своё лобби или кастомка) — general.sandbox = true",
                kind="warn",
                source=self.key,
            )
            return

        for offset, ability in zip(offsets, sequence):
            self.rt.actions(f"cast {ability} @ +{offset:.2f}s")
        self.rt.notify(
            title=f"Комбо запущено: {len(sequence)} шагов",
            text=", ".join(sequence),
            kind="action",
            source=self.key,
        )
