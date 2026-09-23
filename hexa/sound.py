"""Звуковые уведомления: слышно без сворачивания игры.

Только stdlib (winsound на Windows). Вне Windows — тихо, без падений.
Бипаем только важное (timer/warn/action), обычный info-спам молчит.
"""
from __future__ import annotations


def beep(kind: str = "timer") -> None:
    try:
        import winsound  # type: ignore
    except ImportError:
        return
    try:
        if kind == "timer":
            winsound.Beep(880, 150)
        elif kind == "warn":
            winsound.Beep(440, 250)
        elif kind == "action":
            winsound.Beep(660, 120)
    except RuntimeError:
        pass
