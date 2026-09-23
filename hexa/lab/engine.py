"""Single-writer runtime: priority arbitration, deadlines, cancellation, confirmations."""
from __future__ import annotations

import json
import math
import threading
from copy import deepcopy
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

from .models import Command, GameAdapter, Intent, Kind, Point, Priority, Result, Status
from .modules import Combo, make_modules
from .simulator import Simulator


@dataclass
class Lease:
    source: str
    priority: int
    until: float
    group: str


SCENARIOS = {
    "priority": {"title": "Комбо против фарма", "modules": ["combo", "farm"], "duration": 4,
                 "steps": [(0.8, "combo", "Комбо забирает управление у фарма")]},
    "survival": {"title": "Экстренное восстановление", "modules": ["guardian"], "duration": 1.5,
                 "steps": [(0.4, "damage", "Здоровье героя падает до 28%")]},
    "manual": {"title": "Игрок важнее автоматики", "modules": ["combo", "farm", "micro"], "duration": 2.5,
               "steps": [(0.2, "combo", "Старт четырёхшагового комбо"),
                         (1.0, "manual", "Игрок перехватывает управление")]},
    "micro": {"title": "Два юнита, две задачи", "modules": ["micro"], "duration": 3,
              "steps": [(0.3, "hurt_summon", "Искра I получает критический урон")]},
}


def finite_number(value, low: float, high: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name}: ожидается число от {low:g} до {high:g}")
    return float(value)


class Engine:
    def __init__(self, adapter: GameAdapter | None = None, config_path: Path | None = None,
                 plugins: list | None = None, plugin_problems: list[str] | None = None) -> None:
        self.lock = threading.RLock()
        self.adapter = adapter or Simulator()
        self.config_path = config_path
        self.modules = make_modules()
        for module in plugins or []:
            self.modules[module.key] = module
        self.plugin_keys = {m.key for m in plugins or []}
        self.plugin_problems = list(plugin_problems or [])
        self.speed = 1.0
        self.run_id = 0
        self._seq = 0
        self._event_seq = 0
        self.reset()
        if config_path and config_path.exists():
            try:
                self.import_config(json.loads(config_path.read_text("utf-8")), save=False)
            except (ValueError, TypeError, KeyError, OSError):
                self.log("warning", "config", "Конфиг не прочитан — используются настройки по умолчанию")
        for problem in self.plugin_problems:
            self.log("warning", "plugins", problem)
        extra = [m for m in self.modules.values() if m.key in self.plugin_keys]
        if extra:
            names = ", ".join(f"{m.title} (P{m.priority})" for m in extra)
            self.log("success", "plugins", f"Загружены плагины: {names}")

    @property
    def now(self) -> float:
        return self.adapter.observe().time

    def log(self, level: str, source: str, text: str) -> None:
        self._event_seq += 1
        self.events.append({"id": self._event_seq, "time": round(self.now, 3),
                            "level": level, "source": source, "text": text})

    def reset(self) -> None:
        with self.lock:
            self.adapter.reset()
            for m in self.modules.values():
                m.reset()
            self.pending: dict[int, Command] = {}
            self.history: deque[Command] = deque(maxlen=300)
            self.events: deque[dict] = deque(maxlen=160)
            self.counts: Counter = Counter()
            self.leases: dict[str, Lease] = {}
            self.busy: dict[str, float] = {}
            self.manual_until = 0.0
            self.paused = False
            self.selected = "enemy-1"
            self.scenario: dict | None = None
            self.run_id += 1
            self.log("info", "engine", "Полигон готов. Подключён симулятор, не клиент Dota")

    def submit(self, intent: Intent) -> Command:
        """Called only while holding the engine lock (also public for deterministic tests)."""
        if len(self.pending) >= 128:
            raise ValueError("Очередь заполнена")
        if intent.kind not in self.adapter.capabilities.actions:
            raise ValueError("Адаптер не поддерживает эту команду")
        if intent.expires < intent.due:
            raise ValueError("Дедлайн не может быть раньше запланированного времени")
        self._seq += 1
        command = Command(self._seq, intent, self.now)
        self.pending[command.id] = command
        return command

    def _finish(self, command: Command, status: Status, reason: str) -> None:
        self.pending.pop(command.id, None)
        command.status, command.reason, command.finished = status, reason, self.now
        self.history.append(command)
        self.counts[status.value] += 1
        level = "success" if status == Status.EXECUTED else "warning" if status in {Status.REJECTED, Status.EXPIRED} else "info"
        self.log(level, command.intent.source, f"#{command.id:03d} · {reason}")

    def cancel(self, predicate, reason: str) -> int:
        commands = [c for c in self.pending.values() if predicate(c.intent)]
        for command in commands:
            self._finish(command, Status.CANCELLED, reason)
        return len(commands)

    def _release_leases(self) -> None:
        for actor, lease in list(self.leases.items()):
            if self.now >= lease.until or not any(c.intent.group == lease.group for c in self.pending.values()):
                self.leases.pop(actor, None)
                self.log("info", "engine", "Комбо освободило героя — фоновые модули могут продолжить")

    def trigger_combo(self) -> int:
        module = self.modules["combo"]
        if not module.enabled:
            raise ValueError("Сначала включи модуль «Комбо»")
        if not module.requires <= self.adapter.capabilities.actions:
            raise ValueError("Адаптер не поддерживает комбо")
        if self.now < self.manual_until:
            raise ValueError("Активен ручной контроль. Дождись его завершения")
        if "hero" in self.leases:
            raise ValueError("Предыдущее комбо ещё выполняется")
        assert isinstance(module, Combo)
        group = f"combo-{self.run_id}-{self._seq + 1}"
        intents = module.sequence(self.adapter.observe(), self.selected, group)
        self.cancel(lambda i: i.actor == "hero" and i.priority < Priority.COMBO,
                    "Отменено: приоритет комбо выше")
        self.adapter.stop_orders("farm")
        self.leases["hero"] = Lease("combo", Priority.COMBO, self.now + 2.6, group)
        for intent in intents:
            self.submit(intent)
        self.log("info", "combo", "Комбо принято: 4 шага. Герой зарезервирован, фарм ожидает")
        return len(intents)

    def manual_override(self) -> int:
        count = self.cancel(lambda i: i.source != "manual", "Отменено: игрок перехватил управление")
        self.leases.clear()
        self.busy.clear()
        self.adapter.stop_orders()
        self.manual_until = self.now + 4
        self.log("info", "manual", f"Ручной контроль на 4 с · отменено команд: {count}")
        return count

    def dispatch(self) -> None:
        due = sorted((c for c in self.pending.values() if c.intent.due <= self.now + 1e-8),
                     key=lambda c: (-c.intent.priority, c.intent.due, c.id))
        for command in due:
            if command.id not in self.pending:
                continue
            i = command.intent
            if self.now > i.expires + 1e-8:
                self._finish(command, Status.EXPIRED, "Дедлайн истёк — устаревший приказ не исполняется")
                if i.group:
                    self.cancel(lambda other: other.group == i.group, "Последовательность остановлена: истёк дедлайн")
                continue
            if self.now < self.manual_until and i.source != "manual":
                self._finish(command, Status.CANCELLED, "Ручной контроль имеет высший приоритет")
                continue
            lease = self.leases.get(i.actor)
            if lease and i.source != lease.source and i.priority < lease.priority:
                self._finish(command, Status.REJECTED, "Герой занят более приоритетным комбо")
                continue
            if self.busy.get(i.actor, 0) > self.now and i.kind not in {Kind.ITEM, Kind.STOP}:
                continue
            try:
                result = self.adapter.execute(command)
            except Exception as exc:
                result = Result(False, f"Ошибка адаптера: {type(exc).__name__}: {exc}")
            self._finish(command, Status.EXECUTED if result.ok else Status.REJECTED, result.reason)
            if result.ok and result.busy_for:
                self.busy[i.actor] = self.now + result.busy_for
            if not result.ok and i.group:
                self.cancel(lambda other: other.group == i.group, "Последовательность остановлена после отказа адаптера")
        self._release_leases()

    def tick(self, seconds: float) -> None:
        with self.lock:
            if self.paused:
                return
            self.adapter.advance(seconds * self.speed)
            self._run_scenario_steps()
            self._release_leases()
            world = self.adapter.observe()
            if world.time >= self.manual_until:
                for module in self.modules.values():
                    if not module.enabled or not module.requires <= self.adapter.capabilities.actions:
                        continue
                    if module.key == "micro" and not self.adapter.capabilities.multi_unit:
                        continue
                    if module.key == "farm" and "hero" in self.leases:
                        continue
                    try:
                        for intent in module.plan(world, self.selected):
                            # Deduplicate outstanding automatic commands, never combo steps.
                            if not any(c.intent.source == intent.source and c.intent.actor == intent.actor
                                       for c in self.pending.values()):
                                self.submit(intent)
                    except Exception as exc:
                        module.enabled = False
                        self.cancel(lambda i: i.source == module.key, "Модуль отключён после ошибки")
                        self.adapter.stop_orders(module.key)
                        self.log("error", module.key, f"Модуль изолирован: {type(exc).__name__}: {exc}")
            self.dispatch()
            self._complete_scenario()

    def configuration(self) -> dict:
        return {"version": 1, "speed": self.speed,
                "modules": {k: {"enabled": m.enabled, "settings": dict(m.settings)} for k, m in self.modules.items()}}

    def save_config(self) -> None:
        if self.config_path:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.config_path.with_suffix(".tmp")
            temp.write_text(json.dumps(self.configuration(), ensure_ascii=False, indent=2), "utf-8")
            temp.replace(self.config_path)

    def set_module(self, key: str, enabled=None, threshold=None, save=True) -> None:
        if key not in self.modules:
            raise ValueError("Неизвестный модуль")
        if enabled is not None and not isinstance(enabled, bool):
            raise ValueError("enabled должен быть boolean")
        if threshold is not None:
            if key != "guardian":
                raise ValueError("Порог HP есть только у автопредметов")
            threshold = finite_number(threshold, 20, 80, "Порог HP")
        module = self.modules[key]
        if enabled is True:
            if not module.requires <= self.adapter.capabilities.actions:
                raise ValueError("Адаптер не поддерживает необходимые действия")
            if key == "micro" and not self.adapter.capabilities.multi_unit:
                raise ValueError("Адаптер не поддерживает управление несколькими юнитами")
        if enabled is not None:
            module.enabled = enabled
            module.reset()
            if not enabled:
                self.cancel(lambda i: i.source == key, "Модуль выключен пользователем")
                self.adapter.stop_orders(key)
                self._release_leases()
            self.log("info", key, f"{module.title}: {'включён' if enabled else 'выключен'}")
        if threshold is not None:
            module.settings["threshold"] = threshold
        if save:
            self.save_config()

    def import_config(self, payload: dict, save=True) -> None:
        if not isinstance(payload, dict) or payload.get("version") != 1 or not isinstance(payload.get("modules"), dict):
            raise ValueError("Нужен конфиг HEXA Lab версии 1")
        speed = finite_number(payload.get("speed", 1), .5, 2, "Скорость")
        validated = []
        for key, spec in payload["modules"].items():
            if key not in self.modules or not isinstance(spec, dict) or not isinstance(spec.get("enabled"), bool):
                raise ValueError("Неверное описание модуля")
            settings = spec.get("settings", {})
            if not isinstance(settings, dict):
                raise ValueError("settings должен быть объектом")
            threshold = finite_number(settings.get("threshold", 40), 20, 80, "Порог HP") if key == "guardian" else None
            module = self.modules[key]
            if spec["enabled"] and (not module.requires <= self.adapter.capabilities.actions or
                                    (key == "micro" and not self.adapter.capabilities.multi_unit)):
                raise ValueError("Конфиг требует неподдерживаемых возможностей адаптера")
            validated.append((key, spec["enabled"], threshold))
        for key, enabled, threshold in validated:
            self.set_module(key, enabled, threshold, save=False)
        self.speed = speed
        if save:
            self.save_config()
        self.log("success", "config", "Конфигурация применена")

    def start_scenario(self, key: str) -> None:
        if key not in SCENARIOS or not isinstance(self.adapter, Simulator):
            raise ValueError("Сценарий недоступен")
        self.reset()
        spec = SCENARIOS[key]
        for m in self.modules.values():
            m.enabled = m.key in spec["modules"]
        self.modules["guardian"].settings["threshold"] = 40
        self.speed = 1
        self.scenario = {"key": key, "title": spec["title"], "status": "running", "duration": spec["duration"],
                         "steps": [{"at": at, "action": action, "title": title, "done": False}
                                   for at, action, title in spec["steps"]]}
        self.log("info", "scenario", f"Сценарий: {spec['title']}. Настройки изменены только для этой сессии")

    def _run_scenario_steps(self) -> None:
        if not self.scenario or self.scenario["status"] != "running":
            return
        for step in self.scenario["steps"]:
            if step["done"] or self.now < step["at"]:
                continue
            step["done"] = True
            try:
                if step["action"] == "combo":
                    self.trigger_combo()
                elif step["action"] == "manual":
                    self.manual_override()
                elif step["action"] == "damage":
                    self.adapter.damage_hero()
                elif step["action"] == "hurt_summon":
                    self.adapter.units["ally-1"].hp = 85
                self.log("info", "scenario", step["title"])
            except ValueError as exc:
                self.log("warning", "scenario", str(exc))

    def _complete_scenario(self) -> None:
        s = self.scenario
        if not s or s["status"] != "running" or self.now < s["duration"]:
            return
        done = [c for c in self.history if c.status == Status.EXECUTED]
        combo = [c for c in done if c.intent.source == "combo"]
        if s["key"] == "priority":
            ok = len(combo) == 4 and not any(c.intent.source == "farm" and .8 <= c.finished <= 2.76 for c in done)
            text = "Все 4 шага исполнены; фарм не вмешался" if ok else "Проверка не пройдена — смотри журнал"
        elif s["key"] == "survival":
            ok = any(c.intent.source == "guardian" for c in done) and self.adapter.observe().hero.hp_fraction > .4
            text = "Предмет сработал после падения HP" if ok else "Предмет не восстановил здоровье"
        elif s["key"] == "manual":
            ok = 0 < len(combo) < 4 and any(c.status == Status.CANCELLED and c.intent.source == "combo" for c in self.history)
            text = "Оставшиеся шаги комбо отменены игроком" if ok else "Проверка перехвата не пройдена"
        else:
            ok = any(c.intent.actor == "ally-1" and c.intent.kind == Kind.MOVE and c.created > .3 for c in done) and any(c.intent.actor == "ally-2" for c in done)
            text = "Раненый юнит отступает; второй продолжает задачу" if ok else "Проверка микроконтроля не пройдена"
        s.update(status="passed" if ok else "failed", result=text)
        self.log("success" if ok else "warning", "scenario", text)

    def control(self, payload: dict) -> dict:
        with self.lock:
            if not isinstance(payload, dict):
                raise ValueError("Ожидается JSON-объект")
            action = payload.get("action")
            if action == "combo":
                self.trigger_combo()
            elif action == "manual":
                self.manual_override()
            elif action == "move":
                point = Point(finite_number(payload.get("x"), 20, 980, "x"),
                              finite_number(payload.get("y"), 20, 580, "y"))
                self.manual_override()
                self.submit(Intent("manual", "hero", Kind.MOVE, Priority.MANUAL,
                                   self.now, self.now + .5, point=point))
            elif action == "damage":
                if not isinstance(self.adapter, Simulator):
                    raise ValueError("Действие доступно только симулятору")
                self.adapter.damage_hero()
                self.log("warning", "scenario", "Тестовый урон: здоровье героя снижено до 28%")
            elif action == "select":
                target = payload.get("target")
                if not isinstance(target, str) or target not in self.adapter.observe().units:
                    raise ValueError("Неизвестный юнит")
                self.selected = target
            elif action == "pause":
                self.paused = not self.paused
            elif action == "speed":
                self.speed = finite_number(payload.get("value"), .5, 2, "Скорость")
                self.save_config()
            elif action == "reset":
                self.reset()
            elif action == "module":
                key = payload.get("key")
                if not isinstance(key, str):
                    raise ValueError("Нужен ключ модуля")
                self.set_module(key, payload.get("enabled"), payload.get("threshold"))
            elif action == "scenario":
                key = payload.get("key")
                if not isinstance(key, str):
                    raise ValueError("Нужен ключ сценария")
                self.start_scenario(key)
            elif action == "import":
                self.import_config(payload.get("config"))
            elif action == "clear_log":
                self.events.clear()
                self.history.clear()
                self.log("info", "engine", "Журнал очищен. Активная очередь сохранена")
            else:
                raise ValueError("Неизвестное действие")
            return {"ok": True, "action": action}

    def snapshot(self, full=False) -> dict:
        with self.lock:
            w = self.adapter.observe()
            units = [{"id": u.id, "name": u.name, "team": u.team, "role": u.role,
                      **u.position.json(), "hp": round(u.hp, 1), "max_hp": u.max_hp,
                      "mana": round(u.mana, 1), "max_mana": u.max_mana,
                      "controllable": u.controllable, "alive": u.alive, "order_source": u.order_source}
                     for u in w.units.values()]
            skills = [{"key": s.key, "title": s.title, "mana": s.mana, "damage": s.damage,
                       "cooldown": s.cooldown, "remaining": round(max(0, s.ready_at - w.time), 2)}
                      for s in w.skills.values()]
            mods = []
            for key, m in self.modules.items():
                supported = m.requires <= self.adapter.capabilities.actions and (key != "micro" or self.adapter.capabilities.multi_unit)
                if not supported:
                    status = "Не поддерживается адаптером"
                elif not m.enabled:
                    status = "Выключен"
                elif self.now < self.manual_until:
                    status = "Управляет игрок"
                elif key == "farm" and "hero" in self.leases:
                    status = "Ожидает комбо"
                elif key == "combo":
                    status = "Выполняется" if "hero" in self.leases else "Ожидает Q"
                elif key == "guardian":
                    remain = max(0, w.items["restore"].ready_at - w.time)
                    status = f"Перезарядка {remain:.1f} с" if remain else f"Следит за HP ≤ {m.settings['threshold']:g}%"
                else:
                    status = "Работает"
                mods.append({"key": key, "title": m.title, "enabled": m.enabled,
                             "priority": int(m.priority), "settings": dict(m.settings),
                             "status": status, "supported": supported,
                             "plugin": key in self.plugin_keys, "description": m.description})
            history = list(self.history) if full else list(self.history)[-30:]
            return {
                "version": "0.2.0-lab", "run_id": self.run_id, "time": round(w.time, 3),
                "paused": self.paused, "speed": self.speed, "selected": self.selected,
                "adapter": {"name": self.adapter.capabilities.name, "mode": self.adapter.capabilities.mode,
                            "connected_to_dota": self.adapter.capabilities.connected_to_dota,
                            "multi_unit": self.adapter.capabilities.multi_unit,
                            "actions": sorted(k.value for k in self.adapter.capabilities.actions)},
                "units": units, "skills": skills,
                "item": {"title": "Восстановление", "remaining": round(max(0, w.items['restore'].ready_at - w.time), 2),
                         "heal": 420, "threshold": self.modules['guardian'].settings['threshold']},
                "modules": mods, "pending": [c.json() for c in sorted(self.pending.values(), key=lambda c: (c.intent.due, -c.intent.priority))],
                "history": [c.json() for c in history], "events": list(self.events)[-(160 if full else 32):],
                "metrics": {"executed": self.counts["executed"], "cancelled": self.counts["cancelled"],
                            "rejected": self.counts["rejected"], "expired": self.counts["expired"],
                            "pending": len(self.pending)},
                "manual_remaining": round(max(0, self.manual_until - w.time), 2),
                "hero_owner": "manual" if self.now < self.manual_until else "combo" if "hero" in self.leases else "farm" if self.modules['farm'].enabled else "idle",
                "scenario": deepcopy(self.scenario), "config": self.configuration(), **self.adapter.presentation(),
            }
