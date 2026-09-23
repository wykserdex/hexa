"""Deterministic tests: no client, network, external packages or wall-clock sleeps."""
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from hexa.config import Config, DEFAULTS, _deep_merge
from hexa.lab.engine import Engine, SCENARIOS
from hexa.lab.models import Capabilities, Intent, Kind, Point, Priority, Status
from hexa.lab.simulator import Simulator


def advance(engine, seconds):
    for _ in range(round(seconds / .05)):
        engine.tick(.05)


def executed(engine, source):
    return [c for c in engine.history if c.intent.source == source and c.status == Status.EXECUTED]


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.engine = Engine()

    def test_commands_are_structured(self):
        self.engine.trigger_combo()
        commands = list(self.engine.pending.values())
        self.assertEqual(len(commands), 4)
        self.assertEqual(len({c.intent.group for c in commands}), 1)
        self.assertTrue(all(c.intent.kind == Kind.CAST for c in commands))
        self.assertEqual(commands[1].intent.ability, 'emp')
        self.assertEqual(commands[1].intent.due, .6)
        self.assertEqual(commands[1].intent.target, 'enemy-1')

    def test_combo_executes_four_acknowledged_steps(self):
        e = self.engine
        e.trigger_combo()
        advance(e, 3)
        self.assertEqual(len(executed(e, 'combo')), 4)
        self.assertAlmostEqual(e.adapter.observe().units['enemy-1'].hp, 1215)
        self.assertFalse(e.leases)
        self.assertFalse(e.pending)

    def test_combo_timing_is_not_just_text(self):
        e = self.engine
        e.trigger_combo()
        advance(e, 2.5)
        for command, expected in zip(executed(e, 'combo'), [0, .6, 1.25, 1.95]):
            self.assertGreaterEqual(command.finished + 1e-8, expected)
            self.assertLessEqual(command.finished, expected + .051)

    def test_farm_yields_hero_and_resumes_after_combo(self):
        e = self.engine
        e.set_module('farm', True)
        advance(e, .6)
        before = e.now
        position = e.adapter.observe().hero.position
        e.trigger_combo()
        advance(e, 1.9)
        self.assertEqual(e.adapter.observe().hero.position, position)
        self.assertFalse([c for c in executed(e, 'farm') if c.finished > before])
        advance(e, 1)
        self.assertTrue([c for c in executed(e, 'farm') if c.finished > before + 1.9])

    def test_manual_override_cancels_remaining_combo(self):
        e = self.engine
        e.trigger_combo()
        advance(e, .5)
        self.assertEqual(e.manual_override(), 3)
        advance(e, 3)
        self.assertEqual(len(executed(e, 'combo')), 1)
        self.assertEqual(sum(c.status == Status.CANCELLED for c in e.history), 3)
        self.assertFalse(e.pending)

    def test_manual_control_stops_and_then_releases_background_modules(self):
        e = self.engine
        e.set_module('farm', True)
        e.manual_override()
        advance(e, 3.9)
        self.assertEqual(len(executed(e, 'farm')), 0)
        advance(e, .3)
        self.assertGreater(len(executed(e, 'farm')), 0)

    def test_manual_move_is_executed_while_automation_is_suspended(self):
        e = self.engine
        old = e.adapter.observe().hero.position
        e.control({'action': 'move', 'x': 100, 'y': 200})
        advance(e, .5)
        self.assertEqual(len(executed(e, 'manual')), 1)
        self.assertLess(e.adapter.observe().hero.position.x, old.x)
        self.assertGreater(e.manual_until, e.now)

    def test_priority_orders_simultaneous_commands(self):
        e = self.engine
        e.adapter.damage_hero()
        e.adapter.units['creep-1'].position = Point(290, 350)
        e.submit(Intent('farm', 'hero', Kind.ATTACK, Priority.FARM, 0, 1, target='creep-1'))
        e.submit(Intent('guardian', 'hero', Kind.ITEM, Priority.SURVIVAL, 0, 1, ability='restore'))
        e.dispatch()
        self.assertEqual(e.history[0].intent.source, 'guardian')
        self.assertEqual(e.history[1].intent.source, 'farm')
        self.assertTrue(all(c.status == Status.EXECUTED for c in e.history))

    def test_item_trigger_threshold(self):
        e = self.engine
        e.set_module('guardian', threshold=20)
        e.adapter.damage_hero()
        advance(e, .4)
        self.assertFalse(executed(e, 'guardian'))
        e.set_module('guardian', threshold=40)
        advance(e, .4)
        self.assertEqual(len(executed(e, 'guardian')), 1)
        self.assertGreater(e.adapter.observe().hero.hp, 700)

    def test_item_cooldown_prevents_spam(self):
        e = self.engine
        e.adapter.damage_hero()
        advance(e, .2)
        e.adapter.damage_hero()
        advance(e, 2)
        self.assertEqual(len(executed(e, 'guardian')), 1)
        advance(e, 13)
        self.assertEqual(len(executed(e, 'guardian')), 2)

    def test_guardian_does_not_break_combo_lease(self):
        e = self.engine
        e.trigger_combo()
        advance(e, .1)
        e.adapter.damage_hero()
        advance(e, 2.5)
        self.assertEqual(len(executed(e, 'guardian')), 1)
        self.assertEqual(len(executed(e, 'combo')), 4)

    def test_disabling_module_cancels_its_commands(self):
        e = self.engine
        e.trigger_combo()
        e.set_module('combo', False)
        advance(e, 3)
        self.assertFalse(executed(e, 'combo'))
        self.assertEqual(sum(c.status == Status.CANCELLED for c in e.history), 4)
        self.assertFalse(e.leases)

    def test_adapter_failure_cancels_rest_of_sequence(self):
        e = self.engine
        e.trigger_combo()
        e.adapter.units['enemy-1'].hp = 0
        advance(e, .1)
        self.assertEqual(sum(c.status == Status.REJECTED for c in e.history), 1)
        self.assertEqual(sum(c.status == Status.CANCELLED for c in e.history), 3)
        self.assertFalse(e.pending)

    def test_expired_command_is_not_executed(self):
        e = self.engine
        e.submit(Intent('test', 'hero', Kind.MOVE, 10, 0, .01, point=Point(100, 100)))
        e.tick(.05)
        self.assertEqual(e.history[0].status, Status.EXPIRED)
        self.assertIsNone(e.adapter.units['hero'].goal)

    def test_skill_cooldown_is_checked_by_adapter(self):
        e = self.engine
        for _ in range(2):
            e.submit(Intent('test', 'hero', Kind.CAST, 60, 0, 1, ability='tornado', target='enemy-1'))
        e.dispatch()
        advance(e, .3)
        self.assertEqual(e.history[0].status, Status.EXECUTED)
        self.assertEqual(e.history[1].status, Status.REJECTED)
        self.assertIn('перезарядке', e.history[1].reason)

    def test_observation_is_immutable(self):
        w = self.engine.adapter.observe()
        with self.assertRaises(TypeError):
            w.units['new'] = w.hero
        with self.assertRaises(FrozenInstanceError):
            w.hero.hp = 1

    def test_pause_freezes_game_time(self):
        e = self.engine
        e.control({'action': 'pause'})
        advance(e, 5)
        self.assertEqual(e.now, 0)
        e.control({'action': 'pause'})
        advance(e, 1)
        self.assertAlmostEqual(e.now, 1)

    def test_reset_clears_session_not_preferences(self):
        e = self.engine
        e.set_module('guardian', threshold=55)
        e.trigger_combo()
        advance(e, 1)
        e.reset()
        self.assertEqual(e.now, 0)
        self.assertFalse(e.pending)
        self.assertFalse(e.history)
        self.assertEqual(e.modules['guardian'].settings['threshold'], 55)
        self.assertEqual(e.adapter.observe().hero.mana, 650)

    def test_micro_controls_two_distinct_units(self):
        e = self.engine
        e.set_module('micro', True)
        advance(e, 1)
        self.assertEqual({c.intent.actor for c in executed(e, 'micro')}, {'ally-1', 'ally-2'})
        self.assertFalse(any(c.intent.actor == 'hero' for c in executed(e, 'micro')))

    def test_wounded_summon_retreats(self):
        e = self.engine
        e.set_module('micro', True)
        e.adapter.units['ally-1'].hp = 50
        advance(e, .1)
        c = next(c for c in executed(e, 'micro') if c.intent.actor == 'ally-1')
        self.assertEqual(c.intent.kind, Kind.MOVE)
        self.assertLess(c.intent.point.x, e.adapter.observe().hero.position.x)
        self.assertFalse(c.intent.target)

    def test_module_error_is_isolated(self):
        e = self.engine
        e.set_module('farm', True)
        def broken(*args):
            raise RuntimeError('test fault')
        e.modules['farm'].plan = broken
        e.adapter.damage_hero()
        advance(e, .1)
        self.assertFalse(e.modules['farm'].enabled)
        self.assertTrue(executed(e, 'guardian'))
        self.assertTrue(any(log['level'] == 'error' for log in e.events))

    def test_adapter_capabilities_disable_unsupported_features(self):
        sim = Simulator()
        sim.capabilities = Capabilities('read-only', 'test', actions=frozenset(), multi_unit=False)
        e = Engine(sim)
        with self.assertRaises(ValueError):
            e.set_module('combo', True)
        with self.assertRaises(ValueError):
            e.set_module('micro', True)
        self.assertTrue(all(not m['supported'] for m in e.snapshot()['modules']))

    def test_direct_trigger_respects_capabilities_without_leaking_lease(self):
        e = self.engine
        e.adapter.capabilities = Capabilities('read-only', 'test', actions=frozenset())
        with self.assertRaises(ValueError):
            e.trigger_combo()
        self.assertFalse(e.pending)
        self.assertFalse(e.leases)

    def test_adapter_exception_is_recorded_without_crashing_clock(self):
        e = self.engine
        def broken(command):
            raise RuntimeError('transport failure')
        e.adapter.execute = broken
        e.trigger_combo()
        advance(e, .1)
        self.assertEqual(sum(c.status == Status.REJECTED for c in e.history), 1)
        self.assertEqual(sum(c.status == Status.CANCELLED for c in e.history), 3)
        self.assertFalse(e.pending)
        self.assertGreater(e.now, 0)

    def test_unowned_unit_is_rejected(self):
        e = self.engine
        e.submit(Intent('test', 'enemy-1', Kind.MOVE, 100, 0, 1, point=Point(10, 10)))
        e.dispatch()
        self.assertEqual(e.history[0].status, Status.REJECTED)
        self.assertIn('управления', e.history[0].reason)

    def test_invalid_coordinates_are_rejected_without_side_effects(self):
        for value in [float('nan'), float('inf'), True, -1, '100', None]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.engine.control({'action': 'move', 'x': value, 'y': 100})
                self.assertEqual(self.engine.manual_until, 0)
                self.assertFalse(self.engine.pending)

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            self.engine.set_module('guardian', threshold=200)
        self.assertEqual(self.engine.modules['guardian'].settings['threshold'], 40)

    def test_config_is_atomic_and_persistent(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'lab.json'
            e = Engine(config_path=path)
            e.set_module('guardian', threshold=65)
            e.set_module('farm', True)
            other = Engine(config_path=path)
            self.assertEqual(other.modules['guardian'].settings['threshold'], 65)
            self.assertTrue(other.modules['farm'].enabled)
            self.assertFalse(path.with_suffix('.tmp').exists())

    def test_invalid_import_does_not_partially_apply(self):
        e = self.engine
        before = e.configuration()
        bad = {'version': 1, 'modules': {'farm': {'enabled': True}, 'unknown': {'enabled': True}}}
        with self.assertRaises(ValueError):
            e.import_config(bad)
        self.assertEqual(e.configuration(), before)

    def test_all_four_scenarios_pass(self):
        for key in SCENARIOS:
            with self.subTest(key=key):
                e = Engine()
                e.start_scenario(key)
                advance(e, 5)
                self.assertEqual(e.scenario['status'], 'passed')

    def test_snapshot_is_json_serializable(self):
        e = self.engine
        e.start_scenario('priority')
        advance(e, 2)
        encoded = json.dumps(e.snapshot(full=True), allow_nan=False)
        self.assertIn('pending', encoded)
        self.assertFalse(e.snapshot()['adapter']['connected_to_dota'])


class OriginalConfigRegressionTests(unittest.TestCase):
    def test_separate_configs_do_not_mutate_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            a = Config(Path(d) / 'a.json', autosave=False)
            b = Config(Path(d) / 'b.json', autosave=False)
            initial = DEFAULTS['general']['sandbox']
            a.set(not initial, 'general', 'sandbox')
            a.module('manual_timers')['label'] = 'changed'
            self.assertEqual(b.sandbox, initial)
            self.assertEqual(DEFAULTS['general']['sandbox'], initial)
            self.assertNotEqual(b.module('manual_timers')['label'], 'changed')

    def test_merge_does_not_share_nested_objects(self):
        base = {'a': {'numbers': [1, 2]}, 'b': {'value': 3}}
        override = {'b': {'value': 7}}
        merged = _deep_merge(base, override)
        merged['a']['numbers'].append(3)
        merged['b']['value'] = 10
        self.assertEqual(base['a']['numbers'], [1, 2])
        self.assertEqual(override['b']['value'], 7)


if __name__ == '__main__':
    unittest.main()
