"""Stdlib-only local UI/API. All simulation mutations go through one locked engine."""
from __future__ import annotations

import json
import mimetypes
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .engine import Engine

UI = Path(__file__).parent / "ui"
STATIC = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/style.css": "style.css"}


def handler_for(engine: Engine):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            # No X-Frame-Options / frame-ancestors restrictions: live preview uses an iframe.
            self.end_headers()
            self.wfile.write(body)

        def json(self, status: int, data: dict) -> None:
            self.reply(status, json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/state":
                self.json(200, engine.snapshot())
            elif path == "/api/export":
                self.json(200, engine.snapshot(full=True))
            elif path == "/api/health":
                self.json(200, {"ok": True, "adapter": "simulator", "connected_to_dota": False})
            elif path in STATIC:
                file = UI / STATIC[path]
                content_type = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
                self.reply(200, file.read_bytes(), content_type + "; charset=utf-8")
            else:
                self.json(404, {"error": "Not found"})

        def do_POST(self):
            if urlsplit(self.path).path != "/api/control":
                self.json(404, {"error": "Not found"})
                return
            # No CORS wildcard. JSON + cross-site check prevent browser form CSRF.
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                self.json(403, {"error": "Cross-site requests are not allowed"})
                return
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
                self.json(415, {"error": "Use application/json"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 32768:
                    self.json(413, {"error": "JSON body must be 1–32768 bytes"})
                    return
                def invalid_number(raw):
                    raise ValueError("NaN / Infinity are not valid input")
                payload = json.loads(self.rfile.read(length), parse_constant=invalid_number)
                self.json(200, engine.control(payload))
            except (ValueError, TypeError, UnicodeDecodeError) as exc:
                self.json(400, {"error": str(exc)})
            except OSError:
                self.json(500, {"error": "Не удалось сохранить настройки"})

        def log_message(self, fmt, *args):
            if args and str(args[1] if len(args) > 1 else "").startswith("5"):
                super().log_message(fmt, *args)

    return Handler


def serve(host="127.0.0.1", port=8080, config_path: Path | None = None,
          plugins_dir: Path | None = None) -> None:
    plugins, problems = (None, None)
    if plugins_dir:
        from .plugins import load_plugins

        plugins, problems = load_plugins(plugins_dir)
        print(f"Plugins: loaded {len(plugins)}, problems {len(problems)}", flush=True)
        for problem in problems:
            print(f"  ! {problem}", flush=True)
    engine = Engine(config_path=config_path, plugins=plugins, plugin_problems=problems)
    server = ThreadingHTTPServer((host, port), handler_for(engine))
    server.daemon_threads = True
    stop = threading.Event()

    def clock():
        # Fixed simulation steps: deterministic command timings at any rendering rate.
        step = .05
        deadline = time.monotonic()
        while not stop.is_set():
            engine.tick(step)
            deadline += step
            if deadline < time.monotonic() - .5:
                deadline = time.monotonic()
            stop.wait(max(0, deadline - time.monotonic()))

    ticker = threading.Thread(target=clock, name="hexa-simulation", daemon=True)
    ticker.start()
    print(f"HEXA Lab → http://{host}:{port}", flush=True)
    print("Adapter: LOCAL SIMULATOR. No connection to the Dota client.", flush=True)
    print("One shared arena per process; intended for local development, not public hosting.", flush=True)
    try:
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        ticker.join(timeout=2)
        server.server_close()
