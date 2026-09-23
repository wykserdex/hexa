"""CLI обвязки:

  hexa modules                     список модулей
  hexa hotkeys                     биндинги и конфликты
  hexa demo --minutes 9            прогон без игры: часы, таймеры, хоткеи
  hexa gsi --write-cfg <путь>      сгенерировать gamestate_integration_hexa.cfg
  hexa gsi                         поднять приёмник и ждать Доту
  hexa serve                       GSI + мост действий для кастомки (носитель)
  hexa build-panorama --out build/ собрать патч интерфейса (styling.css, hud.js)
  hexa preview --out menu.html     отрисовать меню обвязки в HTML
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hexa.bridges.panorama import build_patch
from hexa.bridges.sandbox import SandboxTraceSink
from hexa.config import Config
from hexa.hotkeys import HotkeyRegistry
from hexa.menu import MenuModel
from hexa.registry import ModuleRegistry
from hexa.runtime import Runtime
from hexa.timers import fmt_time


def _make_runtime(args: argparse.Namespace) -> tuple[Runtime, ModuleRegistry]:
    config = Config(path=getattr(args, "config", None))
    if getattr(args, "sandbox", False):
        config.set(True, "general", "sandbox")
    runtime = Runtime(config=config, sink=SandboxTraceSink(), verbose=True)
    registry = ModuleRegistry(runtime, config)
    return runtime, registry


# ------------------------------------------------------------------ команды


def cmd_modules(args: argparse.Namespace) -> int:
    runtime, registry = _make_runtime(args)
    print(f"конфиг: {runtime.config.path}")
    print(f"режим: {'песочница' if runtime.sandbox else 'обычный'}\n")
    for key, title, enabled, desc in registry.status_rows():
        print(f"  [{'x' if enabled else ' '}] {key:<16} {title}")
        print(f"        {desc}")
    for key, err in registry.errors:
        print(f"  ! {key}: {err}", file=sys.stderr)
    return 0


def cmd_hotkeys(args: argparse.Namespace) -> int:
    runtime, _ = _make_runtime(args)
    registry = HotkeyRegistry(runtime.config)
    for key, action, desc in registry.rows():
        print(f"  {key:<8} {action:<12} {desc}")
    conflicts = registry.conflicts()
    if conflicts:
        print("\nконфликты:")
        for key, first, second in conflicts:
            print(f"  ! {key}: {first} и {second}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    runtime, registry = _make_runtime(args)
    minutes = args.minutes
    step = args.step

    print(f"демо-прогон {minutes} игровых минут, шаг {step} с")
    print(f"модули: {', '.join(m.key for m in registry.enabled_modules()) or '—'}\n")

    t = 0.0
    hotkeys = {(float(at), name) for at, name in _parse_presses(args.press)}
    end = minutes * 60.0
    while t <= end:
        registry.on_tick(t)          # сначала продвигаем игровые часы
        due = sorted((at, name) for at, name in hotkeys if t >= at)
        for at, name in due:
            print(f"\n>>> нажат хоткей {name} на t={fmt_time(t)}")
            registry.on_hotkey(name)
            hotkeys.discard((at, name))
        t += step

    sink = runtime.sink
    print("\n" + "=" * 62)
    if sink and sink.records:
        print("действия, отправленные в sink (только трейс, игра не тронута):")
        print(sink.dump())
        print("=" * 62)
    print(f"уведомлений: {len(runtime.notifications)} | ошибок модулей: {len(registry.errors)}")
    for key, err in registry.errors[:5]:
        print(f"  ! {key}: {err}")

    if args.preview:
        model = MenuModel(runtime, registry, gsi_status="оффлайн (демо)")
        Path(args.preview).parent.mkdir(parents=True, exist_ok=True)
        Path(args.preview).write_text(model.to_html(), encoding="utf-8")
        print(f"меню: {args.preview}")
    return 0


def cmd_gsi(args: argparse.Namespace) -> int:
    runtime, registry = _make_runtime(args)

    if args.write_cfg:
        from hexa.bridges.gsi import write_cfg

        host = str(runtime.config.get("gsi", "host", default="127.0.0.1"))
        port = int(runtime.config.get("gsi", "port", default=3000))
        path = write_cfg(args.write_cfg, host=host, port=port)
        print(f"[+] конфиг для Доты: {path}")
        print("    положить в: <Steam>/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/")
        print("    запускать Доту с -gamestateintegration")
        return 0

    from hexa.bridges.gsi import GsiReceiver

    def on_state(state) -> None:
        registry.on_state(state)
        registry.on_tick(state.t)
        if runtime.verbose and state.hero:
            print(f"  GSI t={fmt_time(state.t)} {state.hero} hp={state.hp:.0f}/{state.max_hp:.0f}")

    receiver = GsiReceiver(runtime.config, on_state)
    print(f"модули: {', '.join(m.key for m in registry.enabled_modules()) or '—'}")
    receiver.serve_forever()
    return 0


def cmd_build_panorama(args: argparse.Namespace) -> int:
    runtime, _ = _make_runtime(args)
    written = build_patch(args.out, runtime.config)
    print("[+] патч интерфейса собран:")
    for path in written:
        print(f"    {path}")
    print("\nприменение:")
    print("  1. styling.css  -> в Minify как styling.txt")
    print("  2. hexa_hud.js  -> в кастомку / локальное лобби")
    print("  3. cfg          -> в game/dota/cfg/gamestate_integration/")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    runtime, registry = _make_runtime(args)
    registry.on_tick(300.0)  # прогреваем часы, чтобы в превью были события и отметки
    if args.simulate:
        registry.on_hotkey("mark_timer")
        registry.on_hotkey("combo")
    model = MenuModel(runtime, registry, gsi_status=args.gsi_status)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(model.to_html(), encoding="utf-8")
    print(f"[+] меню отрисовано: {out}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """GSI (3000) и мост действий (3001) в одном процессе.

    Именно эта команда превращает обвязку в «носитель»: живой канал в игру открыт,
    а sink действий подключён к очереди. Вне песочницы GuardedSink не пропустит
    ничего, даже если модуль ошибётся.
    """
    from hexa.bridges.gsi import GsiReceiver
    from hexa.bridges.http_bridge import BridgeServer
    from hexa.bridges.sandbox import GuardedSink

    runtime, registry = _make_runtime(args)
    bridge = BridgeServer(
        runtime=runtime,
        registry=registry,
        host=str(runtime.config.get("bridge", "host", default="127.0.0.1")),
        port=int(runtime.config.get("bridge", "port", default=3001)),
    )
    runtime.sink = GuardedSink(sandbox=lambda: runtime.sandbox, queue=bridge.actions)
    bridge.start_background()

    print(f"[+] мост действий: http://{bridge.host}:{bridge.port}/state  (для HUD кастомки)")
    print(f"[+] режим: {'ПЕСОЧНИЦА — действия уходят в игру через мост' if runtime.sandbox else 'обычный — действия только в трейсе'}")
    print(f"[+] модули: {', '.join(m.key for m in registry.enabled_modules()) or '—'}\n")

    def on_state(state) -> None:
        registry.on_state(state)
        registry.on_tick(state.t)
        if state.hero:
            bridge.last_hero = {
                "name": state.hero,
                "hp": state.hp,
                "max_hp": state.max_hp,
                "alive": state.hp > 0,
            }

    receiver = GsiReceiver(runtime.config, on_state)
    try:
        receiver.serve_forever()
    finally:
        bridge.stop()
    return 0


def _parse_presses(raw: list[str]) -> list[tuple[str, str]]:
    """'--press mark_timer@200' -> [(200, 'mark_timer')]"""
    result: list[tuple[str, str]] = []
    for item in raw or []:
        if "@" in item:
            name, at = item.split("@", 1)
            result.append((at, name))
    return result


# ------------------------------------------------------------------ вход


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hexa", description="HEXA — обвязка для Dota 2")
    parser.add_argument("--config", help="путь к config.json (по умолчанию ~/.hexa/config.json)")
    parser.add_argument("--sandbox", action="store_true", help="включить режим песочницы (боты / своё лобби / кастомка)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("modules", help="список модулей").set_defaults(func=cmd_modules)
    sub.add_parser("hotkeys", help="биндинги хоткеев").set_defaults(func=cmd_hotkeys)

    p_demo = sub.add_parser("demo", help="прогон без игры")
    p_demo.add_argument("--minutes", type=float, default=9.0)
    p_demo.add_argument("--step", type=float, default=1.0)
    p_demo.add_argument("--press", nargs="*", default=["mark_timer@200", "combo@360"], help="имитация хоткеев, формат имя@секунда")
    p_demo.add_argument("--preview", help="куда сохранить HTML меню")
    p_demo.set_defaults(func=cmd_demo)

    p_serve = sub.add_parser("serve", help="GSI + мост действий в игру (носитель)")
    p_serve.set_defaults(func=cmd_serve)

    p_gsi = sub.add_parser("gsi", help="приёмник Game State Integration")
    p_gsi.add_argument("--write-cfg", help="только сгенерировать конфиг для Доты")
    p_gsi.set_defaults(func=cmd_gsi)

    p_pan = sub.add_parser("build-panorama", help="собрать патч интерфейса")
    p_pan.add_argument("--out", default="build/panorama")
    p_pan.set_defaults(func=cmd_build_panorama)

    p_prev = sub.add_parser("preview", help="отрисовать меню в HTML")
    p_prev.add_argument("--out", default="build/menu.html")
    p_prev.add_argument("--gsi-status", default="оффлайн (превью)")
    p_prev.add_argument("--simulate", action="store_true", help="сымитировать нажатия: отметка + комбо")
    p_prev.set_defaults(func=cmd_preview)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
