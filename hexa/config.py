"""Конфиг обвязки: один файл, секции по модулям, тумблеры, тема.

Всё, что игрок видит в меню и меняет тумблерами, живёт здесь. Файл — обычный JSON,
поэтому его можно синхронизировать в облако (задел под платную подписку с конфигами).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_HOME = Path(os.environ.get("HEXA_HOME", Path.home() / ".hexa"))
DEFAULT_PATH = DEFAULT_HOME / "config.json"

DEFAULTS: dict[str, Any] = {
    "general": {
        "enabled_modules": ["rune_alerts", "stack_helper", "manual_timers", "sandbox_combo"],
        "notify_seconds_before": 20,
        "sandbox": False,
        "language": "ru",
    },
    "hotkeys": {
        "menu": "INSERT",
        "toggle_mode": "F8",
        "mark_timer": "MOUSE4",
        "combo": "MOUSE5",
    },
    "theme": {
        "accent": "#7dd3fc",
        "hud_scale": 1.0,
        "minimap_scale": 1.0,
        "font": "Radiance",
        "positions": {"timers": "left", "notifications": "right"},
    },
    "gsi": {
        "host": "127.0.0.1",
        "port": 3000,
    },
    "bridge": {
        "host": "127.0.0.1",
        "port": 3001,
    },
    "modules": {
        "rune_alerts": {
            "bounty": True,
            "water": True,
            "power": True,
            "wisdom": True,
            "lotus": True,
        },
        "stack_helper": {"lead_seconds": 15, "nearest_camp_only": True},
        "manual_timers": {"default_lifetime_s": 180, "label": "мина"},
        "sandbox_combo": {
            "offsets": [0.0, 0.9, 1.1, 2.6],
            "sequence": [
                "invoker_tornado",
                "invoker_emp",
                "invoker_chaos_meteor",
                "invoker_deafening_blast",
            ],
        },
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Мержим так, чтобы новые дефолты подхватывались, а пользовательские правки не терялись."""
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    def __init__(self, path: Path | str | None = None, autosave: bool = True) -> None:
        self.path = Path(path) if path else DEFAULT_PATH
        self.autosave = autosave
        self.data: dict[str, Any] = dict(DEFAULTS)

        if self.path.exists():
            try:
                stored = json.loads(self.path.read_text(encoding="utf-8"))
                self.data = _deep_merge(DEFAULTS, stored)
            except (json.JSONDecodeError, OSError):
                # битый конфиг не должен ронять обвязку: стартуем на дефолтах
                self.data = dict(DEFAULTS)

    # ------------------------------------------------------------ доступ

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.data
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def set(self, value: Any, *keys: str) -> None:
        node = self.data
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value
        if self.autosave:
            self.save()

    def module(self, key: str) -> dict:
        """Настройки конкретного модуля (то, что модуль менять не должен в чужой секции)."""
        return self.data.setdefault("modules", {}).setdefault(key, {})

    def toggle_module(self, key: str) -> bool:
        enabled: list[str] = self.data["general"]["enabled_modules"]
        if key in enabled:
            enabled.remove(key)
            state = False
        else:
            enabled.append(key)
            state = True
        if self.autosave:
            self.save()
        return state

    def is_enabled(self, key: str) -> bool:
        return key in self.data["general"]["enabled_modules"]

    @property
    def sandbox(self) -> bool:
        return bool(self.data["general"]["sandbox"])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
