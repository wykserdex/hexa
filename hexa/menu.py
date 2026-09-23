"""Модель меню: то, что открывается по клавише.

Из этой же модели рисуется TUI, HTML-превью и Panorama-панель для кастомки —
чтобы представление о продукте не расходилось между носителями.
"""
from __future__ import annotations

import html
from datetime import datetime

from hexa.registry import ModuleRegistry
from hexa.runtime import Runtime
from hexa.timers import fmt_time

ACCENT_FALLBACK = "#7dd3fc"


class MenuModel:
    def __init__(self, runtime: Runtime, registry: ModuleRegistry, gsi_status: str = "не подключён") -> None:
        self.rt = runtime
        self.registry = registry
        self.gsi_status = gsi_status

    @property
    def accent(self) -> str:
        return str(self.rt.config.get("theme", "accent", default=ACCENT_FALLBACK))

    # ------------------------------------------------------------ текстовая версия

    def to_text(self) -> str:
        lines: list[str] = []
        lines.append("=" * 62)
        lines.append(f"  HEXA  ·  режим: {'ПЕСОЧНИЦА' if self.rt.sandbox else 'обычный'}"
                     f"  ·  GSI: {self.gsi_status}")
        lines.append("=" * 62)

        lines.append("\nМОДУЛИ")
        for key, title, enabled, desc in self.registry.status_rows():
            mark = "[x]" if enabled else "[ ]"
            lines.append(f"  {mark} {key:<16} {title}")
            if desc:
                lines.append(f"      {desc}")

        timers = self.rt.engine.upcoming_rows(120)
        lines.append("\nБЛИЖАЙШИЕ СОБЫТИЯ")
        if timers:
            for title, at, left in timers[:8]:
                lines.append(f"  {at:<7} {title:<16} {left}")
        else:
            lines.append("  —")

        manual = self.rt.engine.manual_rows()
        if manual:
            lines.append("\nАКТИВНЫЕ ОТМЕТКИ")
            for label, created, left in manual:
                lines.append(f"  {label:<10} создан {created}   {left}")

        lines.append("\nХОТКЕИ")
        for key, action, desc in self.rt_hotkeys():
            lines.append(f"  {key:<8} {action:<12} {desc}")

        if self.rt.notifications:
            lines.append("\nПОСЛЕДНИЕ УВЕДОМЛЕНИЯ")
            for note in list(self.rt.notifications)[-6:]:
                lines.append(f"  {note.kind_icon()} {note.line()}")

        if self.registry.errors:
            lines.append("\nОШИБКИ МОДУЛЕЙ")
            for key, err in self.registry.errors[-5:]:
                lines.append(f"  ! {key}: {err}")

        return "\n".join(lines)

    def rt_hotkeys(self) -> list[tuple[str, str, str]]:
        from hexa.hotkeys import HotkeyRegistry

        return HotkeyRegistry(self.rt.config).rows()

    # ------------------------------------------------------------ HTML-версия

    def to_html(self) -> str:
        accent = self.accent
        sandbox = self.rt.sandbox
        mode = "ПЕСОЧНИЦА" if sandbox else "ОБЫЧНЫЙ РЕЖИМ"
        mode_color = "#4ade80" if sandbox else "#fbbf24"

        module_cards = "".join(
            (
                '<div style="display:flex;align-items:center;gap:12px;padding:12px 14px;'
                'border:1px solid #232a36;border-radius:12px;background:#141922">'
                f'<div style="width:38px;height:22px;border-radius:11px;background:{accent if enabled else "#2b3240"};'
                'position:relative;flex:0 0 auto">'
                f'<div style="position:absolute;top:3px;{"right" if enabled else "left"}:3px;width:16px;height:16px;'
                'border-radius:50%;background:#0f1218"></div></div>'
                f'<div style="flex:1"><div style="font-weight:600;color:#e8edf6">{html.escape(title)}</div>'
                f'<div style="color:#7f8a9d;font-size:12.5px;margin-top:2px">{html.escape(desc)}</div></div>'
                f'<div style="color:#5d6675;font-size:11px;letter-spacing:.08em">{html.escape(key)}</div>'
                "</div>"
            )
            for key, title, enabled, desc in self.registry.status_rows()
        )

        upcoming = self.rt.engine.upcoming_rows(150)
        upcoming_rows = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #1b212c">'
            f'<span style="color:#c8d1e0">{html.escape(title)}</span>'
            f'<span style="color:{accent};font-variant-numeric:tabular-nums">{html.escape(at)}</span>'
            f'<span style="color:#6f7a8d;font-size:12px">{html.escape(left)}</span></div>'
            for title, at, left in upcoming[:9]
        ) or '<div style="color:#6f7a8d">пока пусто</div>'

        manual = self.rt.engine.manual_rows()
        manual_rows = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:6px 0;color:#c8d1e0">'
            f'<span>{html.escape(label)}</span><span style="color:#8b96a8">{html.escape(left)}</span></div>'
            for label, _, left in manual
        ) or '<div style="color:#6f7a8d">нет активных отметок</div>'

        notes = "".join(
            f'<div style="padding:8px 10px;border-left:2px solid {accent};background:#141922;margin-bottom:6px">'
            f'<div style="font-size:13px;color:#dbe3ef">{html.escape(note.title)}</div>'
            f'<div style="font-size:11.5px;color:#6f7a8d;margin-top:2px">t={fmt_time(note.t)} · {html.escape(note.source)}</div>'
            "</div>"
            for note in list(self.rt.notifications)[-6:][::-1]
        ) or '<div style="color:#6f7a8d">тишина</div>'

        hotkeys = "".join(
            f'<tr><td style="padding:6px 10px 6px 0;color:#e8edf6"><code style="background:#1b2230;padding:2px 6px;'
            f'border-radius:5px;color:{accent}">{html.escape(key)}</code></td>'
            f'<td style="padding:6px 10px 6px 0;color:#9aa5b7;font-size:12.5px">{html.escape(action)}</td>'
            f'<td style="padding:6px 0;color:#6f7a8d;font-size:12.5px">{html.escape(desc)}</td></tr>'
            for key, action, desc in self.rt_hotkeys()
        )

        return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HEXA · меню обвязки</title></head>
<body style="margin:0;background:#0b0e14;color:#e8edf6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<div style="max-width:1000px;margin:0 auto;padding:26px 20px 70px">

  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
    <div style="display:flex;align-items:center;gap:12px">
      <div style="width:34px;height:34px;border-radius:9px;background:{accent};display:flex;align-items:center;justify-content:center;font-weight:800;color:#0b0e14">H</div>
      <div>
        <div style="font-weight:700;font-size:17px">HEXA</div>
        <div style="color:#6f7a8d;font-size:12px">меню обвязки · открывается по <code style="color:{accent}">{html.escape(str(self.rt.config.get("hotkeys","menu",default="INSERT")))}</code></div>
      </div>
    </div>
    <div style="display:flex;gap:8px;align-items:center">
      <span style="font-size:12px;color:{mode_color};border:1px solid {mode_color}44;background:{mode_color}14;padding:5px 10px;border-radius:20px">{mode}</span>
      <span style="font-size:12px;color:#8b96a8;border:1px solid #232a36;padding:5px 10px;border-radius:20px">GSI: {html.escape(self.gsi_status)}</span>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1.15fr .85fr;gap:18px;margin-top:20px">
    <div>
      <div style="font-size:11px;letter-spacing:.12em;color:#6f7a8d;text-transform:uppercase;margin-bottom:10px">Модули</div>
      <div style="display:flex;flex-direction:column;gap:9px">{module_cards}</div>

      <div style="font-size:11px;letter-spacing:.12em;color:#6f7a8d;text-transform:uppercase;margin:20px 0 8px">Хоткеи</div>
      <div style="background:#141922;border:1px solid #232a36;border-radius:12px;padding:10px 14px">
        <table style="width:100%;border-collapse:collapse">{hotkeys}</table>
      </div>
    </div>

    <div>
      <div style="font-size:11px;letter-spacing:.12em;color:#6f7a8d;text-transform:uppercase;margin-bottom:10px">Ближайшие события</div>
      <div style="background:#141922;border:1px solid #232a36;border-radius:12px;padding:10px 14px">{upcoming_rows}</div>

      <div style="font-size:11px;letter-spacing:.12em;color:#6f7a8d;text-transform:uppercase;margin:20px 0 8px">Активные отметки</div>
      <div style="background:#141922;border:1px solid #232a36;border-radius:12px;padding:10px 14px">{manual_rows}</div>

      <div style="font-size:11px;letter-spacing:.12em;color:#6f7a8d;text-transform:uppercase;margin:20px 0 8px">Уведомления</div>
      {notes}
    </div>
  </div>

  <div style="margin-top:26px;padding-top:14px;border-top:1px solid #1b212c;color:#5d6675;font-size:12px;line-height:1.6">
    Сгенерировано {datetime.now():%Y-%m-%d %H:%M}. Живые данные — официальный GSI-интерфейс Valve
    (только состояние игрока). Модули в песочнице исполняют действия через отдельный sink;
    вне неё автоматизация отключена на уровне рантайма.
  </div>
</div>
</body></html>
"""
