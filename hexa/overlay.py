"""Оверлей поверх игры: маленькое окно всегда сверху, читает live.json.

Запуск ВТОРЫМ процессом, пока приёмник уже работает:
    python -m hexa gsi --sound
    python -m hexa overlay

Окно не лезет в игру, не читает память, только показывает твои таймеры.
Передвинь к краю экрана, игра остаётся в фокусе.
"""
from __future__ import annotations


def run(config=None, interval_ms: int = 500) -> int:
    try:
        import tkinter as tk
    except ImportError:
        print("tkinter недоступен — оверлей не запустить (звук --sound всё равно работает)")
        return 2
    from hexa.live import read_live

    root = tk.Tk()
    root.title("HEXA")
    root.attributes("-topmost", True)
    root.geometry("300x180+1610+80")
    root.configure(bg="#0b0e14")
    try:
        root.wm_attributes("-alpha", 0.92)
    except Exception:
        pass

    clock = tk.Label(root, fg="#7dd3fc", bg="#0b0e14", font=("Consolas", 20, "bold"))
    clock.pack(pady=(8, 2))
    hero = tk.Label(root, fg="#8b96a8", bg="#0b0e14", font=("Consolas", 10))
    hero.pack()
    box = tk.Label(root, fg="#e8edf6", bg="#0b0e14", font=("Consolas", 10), justify="left", anchor="nw")
    box.pack(fill="both", expand=True, padx=10, pady=6)

    def tick() -> None:
        try:
            data = read_live(config)
            clock.config(text=str(data.get("clock", "0:00")))
            h = str(data.get("hero", "")).replace("npc_dota_hero_", "")
            hp, mhp = data.get("hp", 0), data.get("max_hp", 0)
            hero.config(text=f"{h} {hp:.0f}/{mhp:.0f}" if h else "")
            notes = data.get("notes", [])[-5:]
            box.config(text="\n".join(f'{n.get("icon", "·")} {n.get("line", "")}' for n in notes) or "тишина")
        except Exception:
            pass
        root.after(interval_ms, tick)

    tick()
    root.mainloop()
    return 0
