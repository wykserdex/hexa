"""Live-файл: мост между приёмником GSI и оверлеем.

Приёмник пишет `~/.hexa/live.json` при каждом уведомлении и состоянии.
Оверлей (`python -m hexa overlay`) читает файл раз в 500 мс.
Никаких новых портов, только локальный файл.
"""
from __future__ import annotations

import json
from pathlib import Path

from hexa.timers import fmt_time

DEFAULT_LIVE = Path.home() / ".hexa" / "live.json"


def live_path(config=None) -> Path:
    if config is not None:
        try:
            custom = config.get("live", "path", default=None)
        except Exception:
            custom = None
        if custom:
            return Path(str(custom)).expanduser()
    return DEFAULT_LIVE


def write_live(config, runtime, state=None) -> None:
    path = live_path(config)
    try:
        notes = [
            {"icon": n.kind_icon(), "line": n.line(), "t": n.t, "kind": n.kind}
            for n in list(runtime.notifications)[-6:]
        ]
        payload = {
            "time": round(runtime.now, 1),
            "clock": fmt_time(runtime.now),
            "hero": getattr(state, "hero", "") or "",
            "hp": getattr(state, "hp", 0) or 0,
            "max_hp": getattr(state, "max_hp", 0) or 0,
            "notes": notes,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def attach_live(runtime, config, sound: bool = False) -> None:
    """Подписать рантайм: каждое уведомление -> live.json (+ опционально звук)."""
    from hexa.sound import beep

    def on_notify(event) -> None:
        note = (event.payload or {}).get("note")
        write_live(config, runtime)
        if sound and note is not None and getattr(note, "kind", "") in {"timer", "warn", "action"}:
            beep(str(note.kind))

    try:
        runtime.bus.subscribe("notify", on_notify)
    except Exception:
        pass
    write_live(config, runtime)


def read_live(config=None) -> dict:
    path = live_path(config)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"time": 0, "clock": "0:00", "hero": "", "hp": 0, "max_hp": 0, "notes": []}
