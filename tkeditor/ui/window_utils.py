from __future__ import annotations

import tkinter as tk


def center_window(window: tk.Misc) -> None:
    """Center the given window on the current display."""
    window.update_idletasks()
    width = max(window.winfo_width(), window.winfo_reqwidth(), 200)
    height = max(window.winfo_height(), window.winfo_reqheight(), 120)
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
