"""Реестр модулей: находим, биндим, включаем по конфигу, изолируем падения."""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import traceback

import hexa.modules as modules_pkg
from hexa.config import Config
from hexa.module import Module
from hexa.runtime import Runtime


class ModuleRegistry:
    def __init__(self, runtime: Runtime, config: Config, auto_load: bool = True) -> None:
        self.rt = runtime
        self.config = config
        self.modules: dict[str, Module] = {}
        self.errors: list[tuple[str, str]] = []
        if auto_load:
            self.reload()

    # ------------------------------------------------------------ загрузка

    def discover(self) -> list[type[Module]]:
        found: list[type[Module]] = []
        for info in pkgutil.iter_modules(modules_pkg.__path__):
            module = importlib.import_module(f"hexa.modules.{info.name}")
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Module) and obj is not Module and obj.__module__ == module.__name__:
                    found.append(obj)
        return sorted(found, key=lambda cls: cls.key)

    def reload(self) -> None:
        for mod in self.modules.values():
            mod.disable()
        self.modules.clear()
        self.errors.clear()

        for cls in self.discover():
            try:
                instance = cls()
                instance.bind(self.rt)
            except Exception as exc:  # noqa: BLE001
                self.errors.append((cls.key, f"не загрузился: {exc}"))
                continue
            if cls.key in self.modules:
                self.errors.append((cls.key, "дубликат ключа"))
                continue
            self.modules[cls.key] = instance

        for key in self.config.get("general", "enabled_modules", default=[]):
            if key in self.modules:
                self.enable(key)

    # ------------------------------------------------------------ тумблеры

    def enable(self, key: str) -> None:
        module = self.modules[key]
        try:
            module.enable()
        except Exception as exc:  # noqa: BLE001
            self.errors.append((key, f"сбой включения: {exc}"))
            module.enabled = False

    def disable(self, key: str) -> None:
        try:
            self.modules[key].disable()
        except Exception as exc:  # noqa: BLE001
            self.errors.append((key, f"сбой выключения: {exc}"))

    def toggle(self, key: str) -> bool:
        """Тумблер в меню: меняет и состояние модуля, и конфиг."""
        state = self.config.toggle_module(key)
        if state:
            self.enable(key)
        else:
            self.disable(key)
        return state

    def enabled_modules(self) -> list[Module]:
        return [m for m in self.modules.values() if m.enabled]

    # ------------------------------------------------------------ прогон

    def on_state(self, state) -> None:
        for module in self.enabled_modules():
            try:
                module.on_state(state)
            except Exception:  # noqa: BLE001
                line = traceback.format_exc(limit=1).strip().splitlines()[-1]
                self.errors.append((module.key, f"сбой on_state: {line}"))
                self.disable(module.key)

    def on_tick(self, now: float) -> None:
        self.rt.engine.sync(now)
        for module in self.enabled_modules():
            try:
                module.on_tick(now)
            except Exception:  # noqa: BLE001
                line = traceback.format_exc(limit=1).strip().splitlines()[-1]
                self.errors.append((module.key, f"сбой on_tick: {line}"))
                self.disable(module.key)

    def on_hotkey(self, action: str) -> None:
        self.rt.press(action)
        for module in self.enabled_modules():
            try:
                module.on_hotkey(action)
            except Exception as exc:  # noqa: BLE001
                self.errors.append((module.key, f"сбой on_hotkey: {exc}"))

    # ------------------------------------------------------------ для меню

    def status_rows(self) -> list[tuple[str, str, bool, str]]:
        return [
            (mod.key, mod.title, mod.enabled, mod.desc) for mod in self.modules.values()
        ]
