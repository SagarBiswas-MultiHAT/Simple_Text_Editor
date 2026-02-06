from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox

from .window_utils import center_window


class FindReplaceDialog:
    """Find and replace dialog window."""

    def __init__(
        self,
        parent: tk.Tk,
        on_find: Callable[[str, bool], None],
        on_replace: Callable[[str, str, bool], None],
        on_replace_all: Callable[[str, str, bool], None],
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self._parent = parent
        self._on_find = on_find
        self._on_replace = on_replace
        self._on_replace_all = on_replace_all
        self._on_close = on_close

        self._window = tk.Toplevel(parent)
        self._window.title("Find and Replace")
        self._window.resizable(False, False)
        self._window.transient(parent)
        self._window.protocol("WM_DELETE_WINDOW", self.close)

        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.regex_var = tk.BooleanVar(value=False)

        self._build_ui()
        center_window(self._window)

    def _build_ui(self) -> None:
        frame = tk.Frame(self._window, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Find:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.find_var, width=30).grid(
            row=0, column=1, columnspan=3, sticky="ew", pady=2
        )

        tk.Label(frame, text="Replace:").grid(row=1, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.replace_var, width=30).grid(
            row=1, column=1, columnspan=3, sticky="ew", pady=2
        )

        tk.Checkbutton(frame, text="Regex", variable=self.regex_var).grid(
            row=2, column=1, sticky="w", pady=4
        )

        tk.Button(frame, text="Find Next", command=self._handle_find).grid(
            row=3, column=0, padx=2, pady=4
        )
        tk.Button(frame, text="Replace", command=self._handle_replace).grid(
            row=3, column=1, padx=2, pady=4
        )
        tk.Button(frame, text="Replace All", command=self._handle_replace_all).grid(
            row=3, column=2, padx=2, pady=4
        )
        tk.Button(frame, text="Close", command=self.close).grid(
            row=3, column=3, padx=2, pady=4
        )

        frame.grid_columnconfigure(1, weight=1)

    def _handle_find(self) -> None:
        query = self.find_var.get()
        if not query:
            messagebox.showinfo("Find", "Enter text to find.")
            return
        self._on_find(query, self.regex_var.get())

    def _handle_replace(self) -> None:
        query = self.find_var.get()
        if not query:
            messagebox.showinfo("Replace", "Enter text to find.")
            return
        self._on_replace(query, self.replace_var.get(), self.regex_var.get())

    def _handle_replace_all(self) -> None:
        query = self.find_var.get()
        if not query:
            messagebox.showinfo("Replace", "Enter text to find.")
            return
        self._on_replace_all(query, self.replace_var.get(), self.regex_var.get())

    def focus(self) -> None:
        self._window.deiconify()
        self._window.lift()
        self._window.focus_force()

    def close(self) -> None:
        self._window.destroy()
        if self._on_close:
            self._on_close()
