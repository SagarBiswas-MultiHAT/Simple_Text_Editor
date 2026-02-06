from pathlib import Path

import pytest

from tkeditor.config import EditorConfig, load_config, save_config
from tkeditor.io import TextIOError, atomic_write, read_text_file


def test_atomic_write_and_read(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    atomic_write(path, "hello world", encoding="utf-8")
    content, encoding = read_text_file(path)
    assert content == "hello world"
    assert encoding == "utf-8"


def test_utf8_bom_detection(tmp_path: Path) -> None:
    path = tmp_path / "bom.txt"
    path.write_bytes(b"\xef\xbb\xbftext")
    content, encoding = read_text_file(path)
    assert content == "text"
    assert encoding == "utf-8-sig"


def test_binary_detection(tmp_path: Path) -> None:
    path = tmp_path / "bin.dat"
    path.write_bytes(b"\x00\x01\x02")
    with pytest.raises(TextIOError):
        read_text_file(path)


def test_config_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TKEDITOR_CONFIG_DIR", str(tmp_path))
    config = EditorConfig(
        theme="dark",
        font_family="Courier",
        font_size=14,
        autosave_enabled=False,
        autosave_interval=45,
        recent_files=["/tmp/a.txt"],
    )
    save_config(config)
    loaded = load_config()
    assert loaded.theme == "dark"
    assert loaded.font_family == "Courier"
    assert loaded.font_size == 14
    assert loaded.autosave_enabled is False
    assert loaded.autosave_interval == 45
    assert loaded.recent_files == ["/tmp/a.txt"]
