from __future__ import annotations

import os
import tempfile
from pathlib import Path


class TextIOError(Exception):
    """Raised when a file cannot be processed as text."""


def read_text_file(path: Path) -> tuple[str, str]:
    """Read a text file and return content plus detected encoding."""
    data = path.read_bytes()
    if is_binary_bytes(data):
        raise TextIOError("File appears to be binary or non-text.")

    encoding = sniff_encoding(data)
    try:
        text = data.decode(encoding)
    except UnicodeDecodeError as exc:
        raise TextIOError("Unable to decode file with detected encoding.") from exc

    return text, encoding


def write_text_file(path: Path, text: str, encoding: str) -> None:
    """Write text to a file using an atomic write strategy."""
    atomic_write(path, text, encoding)


def sniff_encoding(data: bytes) -> str:
    """Detect text encoding using BOM, defaulting to UTF-8."""
    if data.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return "utf-16"
    return "utf-8"


def is_binary_bytes(data: bytes) -> bool:
    """Simple binary detection using NULL byte presence."""
    return b"\x00" in data


def atomic_write(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Atomically write text to path using a temp file and replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
        ) as handle:
            temp_file = Path(handle.name)
            handle.write(text.encode(encoding))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_file, path)
    finally:
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
