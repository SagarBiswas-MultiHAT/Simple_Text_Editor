from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .io import atomic_write

CONFIG_ENV = "TKEDITOR_CONFIG_DIR"
CONFIG_FILE = "config.json"
RECOVERY_TEXT = "recovery.txt"
RECOVERY_META = "recovery.json"
LOG_FILE = "tkeditor.log"


@dataclass
class EditorConfig:
    theme: str = "light"
    font_family: str = "TkFixedFont"
    font_size: int = 12
    autosave_enabled: bool = True
    autosave_interval: int = 30
    recent_files: list[str] = field(default_factory=list)


def get_config_dir() -> Path:
    env_dir = os.environ.get(CONFIG_ENV)
    if env_dir:
        return Path(env_dir).expanduser()

    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if not base:
            base = str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "TkEditor"

    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "TkEditor"

    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "tkeditor"


def get_config_path() -> Path:
    return get_config_dir() / CONFIG_FILE


def get_recovery_paths() -> tuple[Path, Path]:
    base = get_config_dir()
    return base / RECOVERY_TEXT, base / RECOVERY_META


def get_log_path() -> Path:
    return get_config_dir() / LOG_FILE


def load_config() -> EditorConfig:
    path = get_config_path()
    if not path.exists():
        return EditorConfig()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return EditorConfig()

    return _merge_config(EditorConfig(), data)


def save_config(config: EditorConfig) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(config), indent=2, sort_keys=True)
    atomic_write(get_config_path(), payload, encoding="utf-8")


def _merge_config(defaults: EditorConfig, data: dict[str, Any]) -> EditorConfig:
    config = EditorConfig()
    config.theme = str(data.get("theme", defaults.theme))
    config.font_family = str(data.get("font_family", defaults.font_family))
    config.font_size = int(data.get("font_size", defaults.font_size))
    config.autosave_enabled = bool(
        data.get("autosave_enabled", defaults.autosave_enabled)
    )
    config.autosave_interval = int(
        data.get("autosave_interval", defaults.autosave_interval)
    )
    recent = data.get("recent_files", defaults.recent_files)
    if isinstance(recent, list):
        config.recent_files = [str(item) for item in recent]
    else:
        config.recent_files = list(defaults.recent_files)
    return config
