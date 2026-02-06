
# TkEditor

TkEditor is a modern, production-ready Tkinter text editor with autosave recovery,
encoding support, and configurable UI preferences.

![](https://imgur.com/DV7nSsb.png)

## Features

- New, Open, Save, Save As with atomic writes
- Unsaved-change detection with clear prompts
- Undo/Redo, Cut/Copy/Paste, Select All
- Find & Replace with regex support and highlighting
- Live line/column status
- Cross-platform shortcuts (Ctrl/Cmd)
- UTF-8 default with BOM detection; encoding selection on Save As
- Encoding save dialog now presents a dropdown of common encodings and validates the choice
- All windows/dialogs start centered on the current monitor
- Autosave with recovery on next launch
- Light/Dark theme and font customization, persisted settings
- Recent files list
- Rotating file logging for debug mode

## Install

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -e .
```

## Run

```bash
python -m tkeditor
```

## Development

```bash
python -m pip install -e .[dev]
pre-commit install
```

### Tests

```bash
python -m pytest
```

### Lint and Type Check

```bash
python -m ruff check .
python -m isort --check-only .
python -m black --check .
python -m mypy tkeditor
```

## Build (PyInstaller)

```bash
make pyinstaller
```

## Screenshots
 
- Placeholder: light theme
- Placeholder: dark theme

## Configuration

Settings are stored in a JSON file under the OS-specific user config directory.
You can override the location by setting the `TKEDITOR_CONFIG_DIR` environment variable.
