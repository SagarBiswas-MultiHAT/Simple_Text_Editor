from __future__ import annotations

import json
import os
import re
import sys
import threading
from pathlib import Path
from tkinter import filedialog, font, messagebox, simpledialog
import tkinter as tk

from .config import EditorConfig, get_recovery_paths, load_config, save_config
from .io import TextIOError, read_text_file, write_text_file
from .logging import get_logger
from .ui.encoding_dialog import EncodingDialog
from .ui.find_replace import FindReplaceDialog
from .ui.window_utils import center_window

RECENT_LIMIT = 10


class TextEditorApp:
    """Main application class for TkEditor."""

    def __init__(self, root: tk.Tk, config: EditorConfig | None = None) -> None:
        self.root = root
        self.config = config or load_config()
        self.logger = get_logger(debug=bool(os.environ.get("TKEDITOR_DEBUG")))

        self._current_file: Path | None = None
        self._current_encoding = "utf-8"
        self._dirty = False
        self._find_dialog: FindReplaceDialog | None = None

        self._autosave_enabled = self.config.autosave_enabled
        self._autosave_interval = self.config.autosave_interval
        self._autosave_job: str | None = None

        self._modifier = "Command" if sys.platform == "darwin" else "Control"
        self._accel = "Cmd" if sys.platform == "darwin" else "Ctrl"

        self._build_ui()
        self._apply_theme(self.config.theme)
        self._apply_font(self.config.font_family, self.config.font_size)
        self._bind_shortcuts()
        self._update_recent_menu()
        self._check_recovery()
        self._schedule_autosave()
        center_window(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    def _build_ui(self) -> None:
        self.root.title("TkEditor")
        self.root.minsize(640, 480)

        self.menu_bar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New", command=self.new_file, accelerator=f"{self._accel}+N")
        self.file_menu.add_command(label="Open", command=self.open_file, accelerator=f"{self._accel}+O")
        self.file_menu.add_command(label="Save", command=self.save_file, accelerator=f"{self._accel}+S")
        self.file_menu.add_command(label="Save As", command=self.save_file_as, accelerator=f"{self._accel}+Shift+S")
        self.file_menu.add_separator()
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Open Recent", menu=self.recent_menu)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Undo", command=self.undo, accelerator=f"{self._accel}+Z")
        self.edit_menu.add_command(label="Redo", command=self.redo, accelerator=f"{self._accel}+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut, accelerator=f"{self._accel}+X")
        self.edit_menu.add_command(label="Copy", command=self.copy, accelerator=f"{self._accel}+C")
        self.edit_menu.add_command(label="Paste", command=self.paste, accelerator=f"{self._accel}+V")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all, accelerator=f"{self._accel}+A")
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)

        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.search_menu.add_command(label="Find", command=self.open_find_replace, accelerator=f"{self._accel}+F")
        self.search_menu.add_command(label="Replace", command=self.open_find_replace, accelerator=f"{self._accel}+H")
        self.menu_bar.add_cascade(label="Search", menu=self.search_menu)

        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.theme_menu = tk.Menu(self.view_menu, tearoff=0)
        self.theme_menu.add_command(label="Light", command=lambda: self.set_theme("light"))
        self.theme_menu.add_command(label="Dark", command=lambda: self.set_theme("dark"))
        self.view_menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.view_menu.add_command(label="Font Family", command=self.set_font_family)
        self.view_menu.add_command(label="Font Size", command=self.set_font_size)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.autosave_var = tk.BooleanVar(value=self._autosave_enabled)
        self.tools_menu.add_checkbutton(
            label="Autosave",
            variable=self.autosave_var,
            command=self.toggle_autosave,
        )
        self.tools_menu.add_command(
            label="Set Autosave Interval",
            command=self.set_autosave_interval,
        )
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        self.root.config(menu=self.menu_bar)

        self.text = tk.Text(self.root, wrap="word", undo=True, autoseparators=True, maxundo=-1)
        self.text.pack(expand=True, fill="both")
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._update_cursor_position)
        self.text.bind("<ButtonRelease-1>", self._update_cursor_position)
        self.text.tag_configure("find_match", background="#ffe082")

        status_frame = tk.Frame(self.root)
        status_frame.pack(side="bottom", fill="x")
        self.status_label = tk.Label(status_frame, text="Ready", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.pos_label = tk.Label(status_frame, text="Ln 1, Col 1", anchor="e")
        self.pos_label.pack(side="right")

    def _bind_shortcuts(self) -> None:
        mod = self._modifier
        self.root.bind_all(f"<{mod}-n>", lambda _e: self.new_file())
        self.root.bind_all(f"<{mod}-o>", lambda _e: self.open_file())
        self.root.bind_all(f"<{mod}-s>", lambda _e: self.save_file())
        self.root.bind_all(f"<{mod}-Shift-s>", lambda _e: self.save_file_as())
        self.root.bind_all(f"<{mod}-f>", lambda _e: self.open_find_replace())
        self.root.bind_all(f"<{mod}-h>", lambda _e: self.open_find_replace())
        self.root.bind_all(f"<{mod}-a>", lambda _e: self.select_all())
        self.root.bind_all(f"<{mod}-z>", lambda _e: self.undo())
        self.root.bind_all(f"<{mod}-y>", lambda _e: self.redo())
        if sys.platform == "darwin":
            self.root.bind_all(f"<{mod}-Shift-z>", lambda _e: self.redo())
        self.root.bind_all(f"<{mod}-x>", lambda _e: self.cut())
        self.root.bind_all(f"<{mod}-c>", lambda _e: self.copy())
        self.root.bind_all(f"<{mod}-v>", lambda _e: self.paste())

    def _apply_theme(self, theme: str) -> None:
        if theme == "dark":
            bg = "#1e1e1e"
            fg = "#f5f5f5"
            status_bg = "#2b2b2b"
        else:
            bg = "#ffffff"
            fg = "#111111"
            status_bg = "#f0f0f0"

        self.text.config(bg=bg, fg=fg, insertbackground=fg)
        self.status_label.config(bg=status_bg, fg=fg)
        self.pos_label.config(bg=status_bg, fg=fg)

    def _apply_font(self, family: str, size: int) -> None:
        editor_font = font.Font(family=family, size=size)
        self.text.config(font=editor_font)
        self.status_label.config(font=editor_font)
        self.pos_label.config(font=editor_font)

    def _on_modified(self, _event=None) -> None:
        if self.text.edit_modified():
            self._set_dirty(True)
            self.text.edit_modified(False)

    def _set_dirty(self, dirty: bool) -> None:
        if self._dirty != dirty:
            self._dirty = dirty
            self._update_title()

    def _update_title(self) -> None:
        name = self._current_file.name if self._current_file else "Untitled"
        marker = "*" if self._dirty else ""
        self.root.title(f"{name}{marker} - TkEditor")

    def _set_status(self, message: str) -> None:
        self.status_label.config(text=message)

    def _update_cursor_position(self, _event=None) -> None:
        index = self.text.index(tk.INSERT)
        line, col = index.split(".")
        self.pos_label.config(text=f"Ln {line}, Col {int(col) + 1}")

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        choice = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Save before continuing?",
        )
        if choice is None:
            return False
        if choice:
            return self._save_before_close()
        return True

    def _save_before_close(self) -> bool:
        if self._current_file is None:
            return self._save_file_as_sync()
        return self._save_file_sync(self._current_file, self._current_encoding)

    def new_file(self) -> None:
        if not self._confirm_discard():
            return
        self.text.delete("1.0", tk.END)
        self.text.edit_reset()
        self._current_file = None
        self._current_encoding = "utf-8"
        self._set_dirty(False)
        self._set_status("New file")

    def open_file(self) -> None:
        if not self._confirm_discard():
            return
        path_str = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path_str:
            return
        path = Path(path_str)
        self._set_status("Opening...")
        threading.Thread(
            target=self._load_file_thread,
            args=(path,),
            daemon=True,
        ).start()

    def _load_file_thread(self, path: Path) -> None:
        try:
            text, encoding = read_text_file(path)
            self.root.after(0, lambda: self._apply_loaded_file(path, text, encoding))
        except TextIOError as exc:
            self.root.after(0, lambda: self._show_error("Open Error", str(exc)))
        except OSError as exc:
            self.root.after(0, lambda: self._show_error("Open Error", str(exc)))

    def _apply_loaded_file(self, path: Path, text: str, encoding: str) -> None:
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", text)
        self.text.edit_reset()
        self._current_file = path
        self._current_encoding = encoding
        self._set_dirty(False)
        self._add_recent_file(path)
        self._set_status(f"Opened: {path}")
        self._update_cursor_position()

    def save_file(self) -> None:
        if self._current_file is None:
            self.save_file_as()
            return
        self._write_file(self._current_file, self._current_encoding)

    def save_file_as(self) -> None:
        prompt = self._prompt_save_path_and_encoding()
        if not prompt:
            return
        path, encoding = prompt
        self._write_file(path, encoding)

    def _prompt_save_path_and_encoding(self) -> tuple[Path, str] | None:
        path_str = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path_str:
            return None
        dialog = EncodingDialog(self.root, initial=self._current_encoding or "utf-8")
        encoding = dialog.show()
        if not encoding:
            return None
        return Path(path_str), encoding

    def _save_file_sync(self, path: Path, encoding: str) -> bool:
        text = self.text.get("1.0", "end-1c")
        try:
            write_text_file(path, text, encoding)
        except (OSError, TextIOError) as exc:
            self._show_error("Save Error", str(exc))
            return False
        self._finish_save(path, encoding)
        return True

    def _save_file_as_sync(self) -> bool:
        prompt = self._prompt_save_path_and_encoding()
        if not prompt:
            return False
        path, encoding = prompt
        return self._save_file_sync(path, encoding)

    def _write_file(self, path: Path, encoding: str) -> None:
        text = self.text.get("1.0", "end-1c")
        self._set_status("Saving...")
        threading.Thread(
            target=self._write_file_thread,
            args=(path, text, encoding),
            daemon=True,
        ).start()

    def _write_file_thread(self, path: Path, text: str, encoding: str) -> None:
        try:
            write_text_file(path, text, encoding)
            self.root.after(0, lambda: self._finish_save(path, encoding))
        except OSError as exc:
            self.root.after(0, lambda: self._show_error("Save Error", str(exc)))
        except TextIOError as exc:
            self.root.after(0, lambda: self._show_error("Save Error", str(exc)))

    def _finish_save(self, path: Path, encoding: str) -> None:
        self._current_file = path
        self._current_encoding = encoding
        self._set_dirty(False)
        self._add_recent_file(path)
        self._clear_recovery()
        self._set_status(f"Saved: {path}")

    def _show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)
        self._set_status(message)

    def _show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)
        self._set_status(message)

    def undo(self) -> None:
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def redo(self) -> None:
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass

    def cut(self) -> None:
        self.text.event_generate("<<Cut>>")

    def copy(self) -> None:
        self.text.event_generate("<<Copy>>")

    def paste(self) -> None:
        self.text.event_generate("<<Paste>>")

    def select_all(self) -> None:
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)

    def open_find_replace(self) -> None:
        if self._find_dialog is None:
            self._find_dialog = FindReplaceDialog(
                self.root,
                on_find=self.find_next,
                on_replace=self.replace_current,
                on_replace_all=self.replace_all,
                on_close=self._on_find_dialog_close,
            )
        else:
            self._find_dialog.focus()

    def _on_find_dialog_close(self) -> None:
        self._find_dialog = None

    def find_next(self, query: str, use_regex: bool) -> None:
        self.text.tag_remove("find_match", "1.0", tk.END)
        start_index = self.text.index(tk.INSERT)
        content = self.text.get("1.0", "end-1c")
        start_offset = int(self.text.count("1.0", start_index, "chars")[0])

        if use_regex:
            try:
                pattern = re.compile(query)
            except re.error as exc:
                self._show_error("Find Error", str(exc))
                return
            match = pattern.search(content, pos=start_offset)
            if not match:
                match = pattern.search(content, pos=0)
            if not match:
                self._show_info("Find", "No matches found.")
                return
            start = match.start()
            end = match.end()
        else:
            match_index = self.text.search(query, start_index, tk.END)
            if not match_index:
                match_index = self.text.search(query, "1.0", tk.END)
            if not match_index:
                self._show_info("Find", "No matches found.")
                return
            start = int(self.text.count("1.0", match_index, "chars")[0])
            end = start + len(query)

        start_idx = self.text.index(f"1.0 + {start} chars")
        end_idx = self.text.index(f"1.0 + {end} chars")
        self.text.tag_add("find_match", start_idx, end_idx)
        self.text.mark_set(tk.INSERT, end_idx)
        self.text.see(start_idx)

    def replace_current(self, query: str, replacement: str, use_regex: bool) -> None:
        self.find_next(query, use_regex)
        if not self.text.tag_ranges("find_match"):
            return
        start, end = self.text.tag_ranges("find_match")
        selected = self.text.get(start, end)
        if use_regex:
            try:
                replaced = re.sub(query, replacement, selected)
            except re.error as exc:
                self._show_error("Replace Error", str(exc))
                return
        else:
            replaced = replacement
        self.text.delete(start, end)
        self.text.insert(start, replaced)
        self._set_dirty(True)

    def replace_all(self, query: str, replacement: str, use_regex: bool) -> None:
        content = self.text.get("1.0", "end-1c")
        if use_regex:
            try:
                new_content, count = re.subn(query, replacement, content)
            except re.error as exc:
                self._show_error("Replace Error", str(exc))
                return
        else:
            count = content.count(query)
            new_content = content.replace(query, replacement)

        if count == 0:
            self._show_info("Replace", "No matches found.")
            return
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", new_content)
        self._set_dirty(True)
        self._show_info("Replace", f"Replaced {count} occurrence(s).")

    def set_theme(self, theme: str) -> None:
        self.config.theme = theme
        self._apply_theme(theme)
        save_config(self.config)

    def set_font_family(self) -> None:
        family = simpledialog.askstring(
            "Font Family", "Enter font family:", initialvalue=self.config.font_family
        )
        if not family:
            return
        self.config.font_family = family
        self._apply_font(self.config.font_family, self.config.font_size)
        save_config(self.config)

    def set_font_size(self) -> None:
        size = simpledialog.askinteger(
            "Font Size", "Enter font size:", initialvalue=self.config.font_size
        )
        if not size or size <= 0:
            return
        self.config.font_size = size
        self._apply_font(self.config.font_family, self.config.font_size)
        save_config(self.config)

    def toggle_autosave(self) -> None:
        self._autosave_enabled = self.autosave_var.get()
        self.config.autosave_enabled = self._autosave_enabled
        save_config(self.config)
        self._set_status("Autosave enabled" if self._autosave_enabled else "Autosave disabled")

    def set_autosave_interval(self) -> None:
        interval = simpledialog.askinteger(
            "Autosave Interval",
            "Enter autosave interval in seconds:",
            initialvalue=self._autosave_interval,
        )
        if not interval or interval <= 0:
            return
        self._autosave_interval = interval
        self.config.autosave_interval = interval
        save_config(self.config)
        self._schedule_autosave()
        self._set_status(f"Autosave interval set to {interval}s")

    def _schedule_autosave(self) -> None:
        if self._autosave_job:
            self.root.after_cancel(self._autosave_job)
        self._autosave_job = self.root.after(self._autosave_interval * 1000, self._autosave_tick)

    def _autosave_tick(self) -> None:
        if self._autosave_enabled and self._dirty:
            text = self.text.get("1.0", "end-1c")
            threading.Thread(
                target=self._autosave_thread,
                args=(text,),
                daemon=True,
            ).start()
        self._schedule_autosave()

    def _autosave_thread(self, text: str) -> None:
        recovery_text, recovery_meta = get_recovery_paths()
        meta = {
            "path": str(self._current_file) if self._current_file else "",
            "encoding": self._current_encoding,
        }
        try:
            write_text_file(recovery_text, text, "utf-8")
            write_text_file(recovery_meta, json.dumps(meta, indent=2), "utf-8")
        except OSError:
            pass

    def _check_recovery(self) -> None:
        recovery_text, recovery_meta = get_recovery_paths()
        if not recovery_text.exists():
            return
        if recovery_text.stat().st_size == 0:
            self._clear_recovery()
            return

        if messagebox.askyesno(
            "Recovery",
            "An autosave recovery file was found. Recover it?",
        ):
            try:
                text, _ = read_text_file(recovery_text)
                meta = {}
                if recovery_meta.exists():
                    meta = json.loads(recovery_meta.read_text(encoding="utf-8"))
                self.text.delete("1.0", tk.END)
                self.text.insert("1.0", text)
                self.text.edit_reset()
                self._current_file = Path(meta.get("path")) if meta.get("path") else None
                self._current_encoding = meta.get("encoding") or "utf-8"
                self._set_dirty(True)
                self._set_status("Recovery loaded. Please save your work.")
            except (OSError, json.JSONDecodeError, TextIOError) as exc:
                self._show_error("Recovery Error", str(exc))
        else:
            self._clear_recovery()

    def _clear_recovery(self) -> None:
        recovery_text, recovery_meta = get_recovery_paths()
        for path in (recovery_text, recovery_meta):
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass

    def _add_recent_file(self, path: Path) -> None:
        path_str = str(path)
        recent = [p for p in self.config.recent_files if p != path_str]
        recent.insert(0, path_str)
        self.config.recent_files = recent[:RECENT_LIMIT]
        save_config(self.config)
        self._update_recent_menu()

    def _update_recent_menu(self) -> None:
        self.recent_menu.delete(0, tk.END)
        if not self.config.recent_files:
            self.recent_menu.add_command(label="No recent files", state="disabled")
            return
        for path_str in self.config.recent_files:
            self.recent_menu.add_command(
                label=path_str,
                command=lambda p=path_str: self._open_recent(p),
            )

    def _open_recent(self, path_str: str) -> None:
        path = Path(path_str)
        if not path.exists():
            self._show_info("Recent Files", "File not found, removing from list.")
            self.config.recent_files = [p for p in self.config.recent_files if p != path_str]
            save_config(self.config)
            self._update_recent_menu()
            return
        if not self._confirm_discard():
            return
        self._set_status("Opening...")
        threading.Thread(target=self._load_file_thread, args=(path,), daemon=True).start()

    def about(self) -> None:
        messagebox.showinfo("About", "TkEditor\nA simple, modern Tkinter text editor.")

    def on_exit(self) -> None:
        if not self._confirm_discard():
            return
        save_config(self.config)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = TextEditorApp(root)
    app._update_title()
    root.mainloop()
