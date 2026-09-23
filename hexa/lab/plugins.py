"""Загрузка внешних модулей-плагинов из каталога.

Идея заимствована из черновика «Гексагон», но контракт жёстче — исправлены
найденные там дефекты:

- плагин — это подкласс LabModule, определённый в самом файле; реимпорт чужих
  классов игнорируется, дубли невозможны (в черновике каждый плагин создавался
  дважды, а импорт базового класса вообще отсутствовал);
- один экземпляр на класс; конструктор без аргументов, настройки приходят
  из конфига полигона (в черновике config.ini не читался вовсе);
- приоритет ограничен диапазоном 1..89: плагин не может встать выше
  автопредметов (P90) и ручного контроля игрока (P100);
- ключ обязан быть уникальным — конфликт с встроенным модулем отклоняется;
- сбои изолирует сам движок: исключение в plan() отключает модуль, отменяет
  его команды и не роняет общий цикл.

Песочницы нет: плагин исполняется с полными правами процесса. Подключай
только код, который написал сам или прочитал.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from .models import Kind
from .modules import LabModule

PRIORITY_MIN, PRIORITY_MAX = 1, 89
BUILTIN_KEYS = frozenset({"combo", "guardian", "farm", "micro"})


def _import_file(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"не читается как python-модуль: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _plugin_classes(module: ModuleType) -> list[type[LabModule]]:
    """Только классы, определённые в этом файле. Реимпорты не считаются плагинами."""
    return [
        obj
        for obj in vars(module).values()
        if isinstance(obj, type)
        and issubclass(obj, LabModule)
        and obj is not LabModule
        and obj.__module__ == module.__name__
    ]


def _validate(cls: type[LabModule], taken: set[str]) -> LabModule:
    key = cls.key
    if not isinstance(key, str) or not key.strip():
        raise ValueError("key должен быть непустой строкой")
    if key in BUILTIN_KEYS or key in taken:
        raise ValueError(f"ключ «{key}» уже занят")
    if not isinstance(cls.title, str) or not cls.title.strip():
        raise ValueError("title должен быть непустой строкой")
    if isinstance(cls.priority, bool) or not isinstance(cls.priority, int) \
            or not PRIORITY_MIN <= cls.priority <= PRIORITY_MAX:
        raise ValueError(f"priority должен быть целым от {PRIORITY_MIN} до {PRIORITY_MAX}, "
                         f"получено {cls.priority!r}")
    try:
        requires = frozenset(cls.requires)
    except TypeError:
        raise ValueError("requires должен быть набором Kind") from None
    if not all(isinstance(kind, Kind) for kind in requires):
        raise ValueError("requires должен содержать только Kind")
    cls.requires = requires
    cls.origin = "plugin"
    return cls()


def load_plugins(directory: Path | str) -> tuple[list[LabModule], list[str]]:
    """Читает каталог и возвращает (готовые модули, список проблем).

    Проблема в одном файле не мешает остальным: файл пропускается с понятным
    описанием, движок продолжит работу на встроенных модулях.
    """
    directory = Path(directory)
    modules: list[LabModule] = []
    problems: list[str] = []
    if not directory.is_dir():
        return modules, [f"Каталог плагинов не найден: {directory}"]
    taken: set[str] = set()
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("__"):
            continue
        try:
            holder = _import_file(f"hexa_user_plugins.{path.stem}", path)
            for cls in _plugin_classes(holder):
                instance = _validate(cls, taken)
                modules.append(instance)
                taken.add(instance.key)
        except Exception as exc:  # изоляция: один плохой файл не роняет остальные
            problems.append(f"{path.name}: {type(exc).__name__}: {exc}")
    return modules, problems
