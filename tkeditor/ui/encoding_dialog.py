from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .window_utils import center_window

ENCODING_CHOICES = [
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "iso-8859-1",
    "cp1252",
    "ascii",
]


class EncodingDialog:
    """Modal dialog that lets the user pick or enter an encoding."""

    def __init__(self, parent: tk.Tk, initial: str = "utf-8") -> None:
        self._parent = parent
        self._result: str | None = None

        self._window = tk.Toplevel(parent)
        self._window.title("Encoding")
        self._window.resizable(False, False)
        self._window.transient(parent)
        self._window.grab_set()
        self._window.protocol("WM_DELETE_WINDOW", self.close)

        self.encoding_var = tk.StringVar(value=initial)
        self._build_ui()
        center_window(self._window)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self._window, padding=36)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Choose encoding:").grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(
            frame,
            textvariable=self.encoding_var,
            values=ENCODING_CHOICES,
            state="normal",
        )
        combo.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        combo.bind("<KeyRelease>", self._sanitize)
        combo.focus()

        button_frame = ttk.Frame(frame)
        # change spaces between choose encoding dropbox and ok/cancel buttons
        button_frame.grid(row=1, column=0, columnspan=2, pady=(35, 0))
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(
            side="left", padx=4
        )
        ttk.Button(button_frame, text="Cancel", command=self.close).pack(
            side="left", padx=4
        )

        self._window.bind("<Return>", lambda event: self._on_ok())
        self._window.bind("<Escape>", lambda event: self.close())

    def _sanitize(self, _event: tk.Event | None = None) -> None:
        value = self.encoding_var.get()
        self.encoding_var.set(value.strip())

    def _on_ok(self) -> None:
        encoding = self.encoding_var.get().strip()
        if not encoding:
            messagebox.showinfo("Encoding", "Please enter an encoding.")
            return
        try:
            "".encode(encoding)
        except LookupError:
            messagebox.showerror("Encoding Error", f"Unknown encoding: {encoding}")
            return
        self._result = encoding
        self.close()

    def close(self) -> None:
        if self._window.grab_current() is self._window:
            self._window.grab_release()
        self._window.destroy()

    def show(self) -> str | None:
        self._window.wait_window()
        return self._result
