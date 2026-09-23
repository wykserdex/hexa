"""Мост в клиент: официальный Game State Integration.

Valve сам отдаёт состояние игры по HTTP. Мы только слушаем: сервер не пишет в игру,
не читает память и не модифицирует файлы. В ranked-GSI приходит только собственный
игрок — так что этот канал физически не может дать скрытую информацию.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from hexa.config import Config

CFG_TEMPLATE = """// HEXA · Game State Integration
// Положить в: <Steam>/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/
// Запускать Доту с параметром -gamestateintegration
"HEXA Integration"
{{
    "uri"          "http://{host}:{port}/gsi"
    "timeout"      "5.0"
    "buffer"       "0.1"
    "throttle"     "0.1"
    "heartbeat"    "10.0"
    "data"
    {{
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "events"        "1"
    }}
}}
"""


@dataclass
class GsiState:
    """Только то, что Valve отдаёт игроку. Никаких врагов и скрытых данных."""

    t: float = 0.0
    game_time: float = 0.0
    phase: str = ""
    hero: str = ""
    hero_level: int = 0
    hp: float = 0.0
    max_hp: float = 0.0
    mana: float = 0.0
    max_mana: float = 0.0
    player: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def in_game(self) -> bool:
        return self.phase in {"DOTA_GAMERULES_STATE_GAME_IN_PROGRESS", "DOTA_GAMERULES_STATE_STRATEGY_TIME"}


def parse(payload: dict[str, Any]) -> GsiState:
    map_data = payload.get("map") or {}
    hero_data = payload.get("hero") or {}
    player_data = payload.get("player") or {}

    clock = map_data.get("clock_time")
    game_time = float(map_data.get("game_time") or 0.0)
    t = float(clock) if clock is not None else game_time

    return GsiState(
        t=t,
        game_time=game_time,
        phase=str(map_data.get("name", "")),
        hero=str(hero_data.get("name", "")),
        hero_level=int(hero_data.get("level") or 0),
        hp=float(hero_data.get("health") or 0),
        max_hp=float(hero_data.get("max_health") or 0),
        mana=float(hero_data.get("mana") or 0),
        max_mana=float(hero_data.get("max_mana") or 0),
        player=str(player_data.get("name", "")),
        raw=payload,
    )


def write_cfg(path: Path | str, host: str = "127.0.0.1", port: int = 3000) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(CFG_TEMPLATE.format(host=host, port=port), encoding="utf-8")
    return target


class _Handler(BaseHTTPRequestHandler):
    on_state: Callable[[GsiState], None] | None = None

    def do_POST(self) -> None:  # noqa: N802 - требование stdlib
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        state = parse(payload)
        if state.t and self.on_state:
            self.on_state(state)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args: Any) -> None:  # тишина в консоли: шум от Доты бесполезен
        return


class GsiReceiver:
    """HTTP-приёмник. Работает в потоке, останавливается по stop()."""

    def __init__(self, config: Config, on_state: Callable[[GsiState], None]) -> None:
        self.config = config
        self.host = str(config.get("gsi", "host", default="127.0.0.1"))
        self.port = int(config.get("gsi", "port", default=3000))
        self.on_state = on_state
        self._httpd: ThreadingHTTPServer | None = None
        self.received = 0

    def serve_forever(self) -> None:
        handler = type("HexaHandler", (_Handler,), {"on_state": self._wrapped})
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        print(f"[+] GSI слушает http://{self.host}:{self.port}/gsi")
        print("    в Доте: -gamestateintegration, конфиг — hexa gsi --write-cfg <путь>")
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[+] остановлено")
        finally:
            self.stop()

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    def _wrapped(self, state: GsiState) -> None:
        self.received += 1
        self.on_state(state)
