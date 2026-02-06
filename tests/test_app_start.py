import pytest


def test_app_smoke() -> None:
    tk = pytest.importorskip("tkinter")
    from tkeditor.app import TextEditorApp
    from tkeditor.config import EditorConfig

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("tkinter not available in this environment")
    root.withdraw()
    TextEditorApp(root, EditorConfig())
    root.update_idletasks()
    root.destroy()
