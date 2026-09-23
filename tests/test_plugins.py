"""Плагины: загрузка из каталога, изоляция сбоев, участие в планировщике."""
import tempfile
import textwrap
import unittest
from pathlib import Path

from hexa.lab.engine import Engine
from hexa.lab.models import Status
from hexa.lab.plugins import load_plugins


def advance(engine, seconds):
    for _ in range(round(seconds / .05)):
        engine.tick(.05)


def executed(engine, source):
    return [c for c in engine.history if c.intent.source == source and c.status == Status.EXECUTED]

GOOD = '''
from hexa.lab.models import Intent, Kind, Point
from hexa.lab.modules import LabModule

class Rally(LabModule):
    key, title = "rally", "Отход"
    priority = 30
    requires = frozenset({Kind.MOVE})

    def __init__(self):
        super().__init__(enabled=False, settings={"threshold": 35})

    def plan(self, world, selected):
        return []

# Реимпорт чужого класса не должен создавать второй плагин.
Imported = LabModule
'''

BAD_PRIORITY = '''
from hexa.lab.modules import LabModule

class Greedy(LabModule):
    key, title, priority = "greedy", "Жадный", 95
'''

DUP_KEY = '''
from hexa.lab.modules import LabModule

class Fake(LabModule):
    key, title = "combo", "Самозванец"
'''

CRASHY = '''
from hexa.lab.modules import LabModule

class Boom(LabModule):
    key, title, priority = "boom", "Взрывается при создании", 20
    def __init__(self):
        raise RuntimeError("нет данных")
'''

BROKEN_SYNTAX = 'class Half(:\n'

ACTION = '''
from hexa.lab.models import Intent, Kind, Point
from hexa.lab.modules import LabModule

class Rally(LabModule):
    key, title, description = "rally", "Отход", "Уводит героя при низком HP"
    priority = 30
    requires = frozenset({Kind.MOVE})

    def __init__(self):
        super().__init__(enabled=False, settings={"threshold": 35, "x": 120, "y": 480})

    def plan(self, world, selected):
        if not self.ready(world.time, .2):
            return []
        hero = world.hero
        if not hero.alive or hero.hp_fraction > .35:
            return []
        return [Intent(self.key, hero.id, Kind.MOVE, self.priority,
                       world.time, world.time + .8, point=Point(120, 480))]
'''

CRYING = '''
from hexa.lab.modules import LabModule

class Crying(LabModule):
    key, title = "crying", "Падает в plan"
    priority = 15

    def plan(self, world, selected):
        raise ZeroDivisionError("плагин сломался")
'''


def write_plugins(**files: str) -> Path:
    root = Path(tempfile.mkdtemp(prefix="hexa-plugins-"))
    for name, source in files.items():
        (root / f"{name}.py").write_text(textwrap.dedent(source), "utf-8")
    return root


class LoaderTests(unittest.TestCase):
    def test_discovery_skips_reimports_and_reports_problems(self):
        root = write_plugins(good=GOOD, bad_priority=BAD_PRIORITY, dup=DUP_KEY,
                             crashy=CRASHY, broken=BROKEN_SYNTAX)
        modules, problems = load_plugins(root)
        self.assertEqual([m.key for m in modules], ["rally"])
        self.assertEqual(modules[0].origin, "plugin")
        self.assertEqual(len(problems), 4)
        joined = " | ".join(problems)
        for fragment in ("bad_priority.py", "dup.py", "crashy.py", "broken.py"):
            self.assertIn(fragment, joined)
        self.assertIn("получено 95", joined)  # причина: приоритет вне диапазона
        self.assertIn("занят", joined)        # причина: конфликт ключа
        self.assertIn("RuntimeError", joined)  # причина: конструктор упал


    def test_missing_directory_is_reported_not_raised(self):
        modules, problems = load_plugins("/nonexistent/hexa-plugins")
        self.assertEqual(modules, [])
        self.assertEqual(len(problems), 1)

    def test_order_is_deterministic_by_filename(self):
        root = write_plugins(b_good=GOOD, a_good=GOOD.replace('"rally"', '"escort"').replace("Отход", "Эскорт"))
        modules, problems = load_plugins(root)
        self.assertEqual([m.key for m in modules], ["escort", "rally"])
        self.assertEqual(problems, [])


class EnginePluginTests(unittest.TestCase):
    def test_plugin_plans_and_survives_engine(self):
        root = write_plugins(rally=ACTION)
        modules, problems = load_plugins(root)
        self.assertEqual(problems, [])
        engine = Engine(plugins=modules)
        engine.set_module("guardian", False)
        engine.set_module("rally", True)
        engine.adapter.damage_hero()
        advance(engine, .5)
        moves = executed(engine, "rally")
        self.assertGreaterEqual(len(moves), 1)
        self.assertEqual(moves[0].intent.point.x, 120)
        snapshot = engine.snapshot()
        row = next(m for m in snapshot["modules"] if m["key"] == "rally")
        self.assertTrue(row["plugin"])
        self.assertEqual(row["description"], "Уводит героя при низком HP")
        self.assertEqual(len(snapshot["modules"]), 5)

    def test_manual_override_still_wins_over_plugin(self):
        root = write_plugins(rally=ACTION)
        engine = Engine(plugins=load_plugins(root)[0])
        engine.set_module("guardian", False)
        engine.set_module("rally", True)
        engine.adapter.damage_hero()
        engine.manual_override()
        advance(engine, .3)
        self.assertEqual(executed(engine, "rally"), [])

    def test_crashing_plugin_is_isolated(self):
        root = write_plugins(crying=CRYING, rally=ACTION)
        engine = Engine(plugins=load_plugins(root)[0])
        engine.set_module("crying", True)
        engine.set_module("rally", True)
        engine.adapter.damage_hero()
        advance(engine, .5)
        self.assertFalse(engine.modules["crying"].enabled)
        self.assertTrue(engine.modules["rally"].enabled)
        self.assertGreaterEqual(len(executed(engine, "rally")), 1)
        self.assertTrue(any("Модуль изолирован" in e["text"] and e["source"] == "crying"
                            for e in engine.events))

    def test_config_roundtrip_with_plugin(self):
        root = write_plugins(rally=ACTION)
        engine = Engine(plugins=load_plugins(root)[0])
        engine.set_module("rally", True, save=False)
        payload = engine.configuration()
        self.assertIn("rally", payload["modules"])
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            import json
            json.dump(payload, handle)
            path = Path(handle.name)
        try:
            restored = Engine(plugins=load_plugins(root)[0], config_path=path)
            self.assertTrue(restored.modules["rally"].enabled)
        finally:
            path.unlink()
        with self.assertRaises(ValueError):
            restored.import_config({"version": 1, "modules": {"unknown": {"enabled": True}}})


if __name__ == "__main__":
    unittest.main()
