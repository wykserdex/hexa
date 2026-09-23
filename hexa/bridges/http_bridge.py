"""Мост рантайма в игру: HTTP-канал между HEXA и аддоном кастомки.

Схема (единственный путь, которым внешний процесс может легально влиять на свою же игру):

    HEXA (Python)  <--HTTP-->  Panorama HUD (клиент)  <--CustomGameEvent-->  серверный Lua

1. Клиент раз в 0.5 с дергает GET /state: получает таймеры, уведомления и очередь действий.
2. Клиент отправляет POST /event: нажатия хоткеев и игровое время.
3. Очередь действий уходит в клиент, клиент пересылает её на сервер игры событием,
   серверный Lua исполняет официальным API. Никакой инъекции: всё внутри твоей кастомки.
"""
from __future__ import annotations

import json
import threading
from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from hexa.timers import fmt_time


@dataclass
class ActionQueue:
    """Очередь действий в игру с монотонной нумерацией: клиент читает от lastSeq+1."""

    maxlen: int = 256
    items: deque = field(default_factory=lambda: deque(maxlen=256))
    seq: int = 0

    def __post_init__(self) -> None:
        self.items = deque(maxlen=self.maxlen)

    def put(self, actions: list[str], t: float = 0.0) -> None:
        self.seq += 1
        self.items.append({"seq": self.seq, "t": round(t, 2), "items": list(actions)})

    def since(self, last_seq: int) -> list[dict]:
        return [entry for entry in self.items if entry["seq"] > last_seq]

    def latest_seq(self) -> int:
        return self.seq

    def clear(self) -> None:
        self.items.clear()


@dataclass
class BridgeServer:
    """HTTP-мост: /state для клиента, /event от клиента, /health для отладки."""

    runtime: Any
    registry: Any
    host: str = "127.0.0.1"
    port: int = 3001
    actions: ActionQueue = field(default_factory=ActionQueue)
    received_events: int = 0
    last_hero: dict = field(default_factory=dict)
    _httpd: ThreadingHTTPServer | None = None
    _thread: threading.Thread | None = None

    # ------------------------------------------------------------ жизненный цикл

    def start_background(self) -> threading.Thread:
        handler = self._make_handler()
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    # ------------------------------------------------------------ состояние для клиента

    def snapshot(self, last_seq: int = 0) -> dict:
        rt, engine = self.runtime, self.runtime.engine
        notes = [
            {"t": round(n.t, 1), "title": n.title, "text": n.text, "kind": n.kind, "source": n.source}
            for n in list(rt.notifications)[-6:]
        ]
        return {
            "seq": self.actions.latest_seq(),
            "t": round(engine.now, 2),
            "game_time": round(engine.now, 2),
            "sandbox": bool(rt.sandbox),
            "hero": self.last_hero,
            "upcoming": [
                {"title": title, "at": at, "left": left} for title, at, left in engine.upcoming_rows(150)
            ],
            "manual": [
                {"label": label, "created": created, "left": left}
                for label, created, left in engine.manual_rows()
            ],
            "notes": notes,
            "actions": self.actions.since(last_seq),
            "errors": [{"key": k, "error": e} for k, e in self.registry.errors[-3:]],
        }

    # ------------------------------------------------------------ обработка событий от клиента

    def handle_event(self, payload: dict) -> dict:
        self.received_events += 1
        kind = str(payload.get("type", ""))

        if kind == "hotkey":
            action = str(payload.get("action", ""))
            if action:
                self.registry.on_hotkey(action)
            return {"ok": True, "handled": "hotkey", "action": action}

        if kind == "tick":
            game_time = float(payload.get("game_time") or 0.0)
            self.registry.on_tick(game_time)
            return {"ok": True, "handled": "tick", "t": round(game_time, 2)}

        if kind == "hero":
            self.last_hero = {
                "name": str(payload.get("name", "")),
                "hp": float(payload.get("hp") or 0),
                "max_hp": float(payload.get("max_hp") or 0),
                "alive": bool(payload.get("alive", True)),
            }
            return {"ok": True, "handled": "hero"}

        return {"ok": False, "error": f"unknown event type {kind!r}"}

    # ------------------------------------------------------------ HTTP

    def _make_handler(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def _json(self, code: int, payload: dict) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                path = self.path.split("?", 1)[0]
                query = self.path.split("?", 1)[1] if "?" in self.path else ""
                last_seq = 0
                for chunk in query.split("&"):
                    if chunk.startswith("since="):
                        try:
                            last_seq = int(chunk.split("=", 1)[1])
                        except ValueError:
                            last_seq = 0

                if path == "/state":
                    self._json(200, bridge.snapshot(last_seq))
                elif path == "/health":
                    self._json(200, {"ok": True, "received": bridge.received_events,
                                     "t": round(bridge.runtime.engine.now, 1)})
                else:
                    self._json(404, {"error": "not found"})

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    payload = json.loads(raw or b"{}")
                except json.JSONDecodeError as exc:
                    self._json(400, {"error": f"bad json: {exc}"})
                    return

                if self.path.startswith("/event"):
                    self._json(200, bridge.handle_event(payload))
                else:
                    self._json(404, {"error": "not found"})

            def log_message(self, *args: Any) -> None:
                return

        return Handler
