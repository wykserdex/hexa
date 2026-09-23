"""Мост в клиент: патч интерфейса (путь Minify: VPK + Panorama).

Что генерируем:
  styling.css      — визуал клиента: акцент, размер панелей, миникарта, шрифт худа.
  hud.js           — Panorama-панель. Работает там, где у нас есть контроль
                     над клиентской логикой (кастомка, локальное лобби). Для ranked
                     применяется только CSS-часть: она не показывает ничего скрытого.
  blacklist.txt    — что вырезать из клиента (формат Minify).
  notes.txt        — подпись патча в интерфейсе Minify.

Что НЕ генерируем: панели с данными о врагах, кулдаунами чужого героя и прочим,
чего игрок не должен видеть. Это и есть граница между кастомизацией и инфо-преимуществом.
"""
from __future__ import annotations

from pathlib import Path

from hexa.bridges.gsi import write_cfg
from hexa.config import Config

CSS_TEMPLATE = """/* HEXA · styling.css — для Minify (styling.txt) */
:root {{
    --hexa-accent: {accent};
    --hexa-hud-scale: {hud_scale};
    --hexa-minimap-scale: {minimap_scale};
}}

#HeroDetails,
#AbilityList,
#ItemsContainer {{
    border-color: var(--hexa-accent);
}}

#minimap {{
    transform: scale(var(--hexa-minimap-scale));
    transform-origin: bottom left;
}}

#AbilityList,
#ItemsContainer {{
    transform: scale(var(--hexa-hud-scale));
    transform-origin: bottom center;
}}

/* Панель таймеров: заполняет hexa_hud.js в кастомке */
#HexaTimersPanel {{
    position: absolute;
    top: {timers_top}px;
    left: {timers_left}px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 10px;
    background-color: rgba(11, 14, 20, 0.72);
    border: 1px solid var(--hexa-accent);
    border-radius: 8px;
    font-family: "{font}", Radiance, sans-serif;
    color: #e8edf6;
}}

#HexaTimersPanel .hexa-row {{
    font-size: 14px;
    white-space: nowrap;
}}

#HexaTimersPanel .hexa-time {{
    color: var(--hexa-accent);
    margin-right: 8px;
}}
"""

HUD_JS_TEMPLATE = """// HEXA · hexa_hud.js — клиентская часть кастомки.
// Тянет состояние у HEXA (`python -m hexa serve`, порт {port}) и шлёт туда игровые события.
// Требует серверный Lua (hexa_server.lua), который отвечает с игровым временем.
(function () {{
    var BASE = "http://{host}:{port}";
    var POLL = 0.5;
    var lastSeq = 0;
    var gameTime = 0;

    function panel() {{
        var p = $("#HexaTimersPanel");
        if (!p) p = $.CreatePanel("Panel", $.GetContextPanel(), "HexaTimersPanel");
        return p;
    }}

    function render(state) {{
        var p = panel();
        p.RemoveAndDeleteChildren();
        (state.upcoming || []).slice(0, 6).forEach(function (row) {{
            var label = $.CreatePanel("Label", p, "");
            label.AddClass("hexa-row");
            label.html = true;
            label.text = '<span class="hexa-time">' + row.at + '</span>' + row.title;
        }});
    }}

    function sendActions(state) {{
        (state.actions || []).forEach(function (action) {{
            if (action.seq <= lastSeq) return;
            lastSeq = action.seq;
            // песочница: действия уходят на сервер игры, исполняет hexa_server.lua
            GameEvents.SendCustomGameEventToServer("hexa_action", {{ items: action.items.join("|") }});
        }});
    }}

    function poll() {{
        $.AsyncWebRequest(BASE + "/state?since=" + lastSeq, {{
            type: "GET",
            callback: function (data) {{
                try {{
                    var state = JSON.parse(data);
                    render(state);
                    sendActions(state);
                }} catch (e) {{}}
            }}
        }});
        // сообщаем HEXA игровое время; его присылает сервер игры в hexa_state
        $.AsyncWebRequest(BASE + "/event", {{
            type: "POST",
            data: JSON.stringify({{ type: "tick", game_time: gameTime }})
        }});
        $.Schedule(POLL, poll);
    }}

    // хоткей: сервер шлёт это событие, когда игрок нажал привязанную клавишу
    GameEvents.Subscribe("hexa_press", function (event) {{
        $.AsyncWebRequest(BASE + "/event", {{
            type: "POST",
            data: JSON.stringify({{ type: "hotkey", action: event.action }})
        }});
    }});

    // игровое время приходит от серверного Lua
    GameEvents.Subscribe("hexa_state", function (event) {{ gameTime = event.game_time || 0; }});

    poll();
}})();
"""

BLACKLIST_TEMPLATE = """# HEXA · blacklist.txt — пути, которые вырезаются из клиента (формат Minify).
# Пусто по умолчанию: ничего не ломаем, добавляй сам при необходимости.
# Пример:
# particles/ui/xxx.vpcf

"""


def build_patch(out_dir: Path | str, config: Config, host: str | None = None, port: int | None = None) -> list[Path]:
    """Порт в конфиге bridges: GSI (3000) и мост действий (3001) — разные вещи."""
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)

    gsi_host = str(config.get("gsi", "host", default="127.0.0.1"))
    gsi_port = int(config.get("gsi", "port", default=3000))
    bridge_host = str(config.get("bridge", "host", default=gsi_host))
    bridge_port = int(config.get("bridge", "port", default=3001))

    accent = str(config.get("theme", "accent", default="#7dd3fc"))
    hud_scale = float(config.get("theme", "hud_scale", default=1.0))
    minimap_scale = float(config.get("theme", "minimap_scale", default=1.0))
    font = str(config.get("theme", "font", default="Radiance"))
    positions = config.get("theme", "positions", default={}) or {}
    timers_left = 18

    written: list[Path] = []

    css = target / "styling.css"
    css.write_text(
        CSS_TEMPLATE.format(
            accent=accent,
            hud_scale=hud_scale,
            minimap_scale=minimap_scale,
            font=font,
            timers_top=18 if positions.get("timers") == "left" else 150,
            timers_left=timers_left,
        ),
        encoding="utf-8",
    )
    written.append(css)

    js = target / "hexa_hud.js"
    js.write_text(HUD_JS_TEMPLATE.format(host=bridge_host, port=bridge_port), encoding="utf-8")
    written.append(js)

    bl = target / "blacklist.txt"
    bl.write_text(BLACKLIST_TEMPLATE, encoding="utf-8")
    written.append(bl)

    notes = target / "notes.txt"
    notes.write_text(
        "HEXA — обвязка для Dota 2.\n"
        "Модули: тайминги рун, окно стака, ручные отметки, песочница.\n"
        "Живые данные — официальный GSI. Действия — через мост и только в песочнице.\n",
        encoding="utf-8",
    )
    written.append(notes)

    cfg = write_cfg(target / "gamestate_integration_hexa.cfg", host=gsi_host, port=gsi_port)
    written.append(cfg)

    return written
