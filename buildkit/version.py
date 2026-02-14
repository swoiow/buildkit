import re
from pathlib import Path
from typing import Optional, Pattern


_VERSION_PATTERNS: list[Pattern[str]] = [
    re.compile(r"(?im)^\s*__?version__?\s*=\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"(?im)^\s*__?version__?\s*=\s*\(([^)]+)\)"),
    re.compile(r"(?im)^\s*__?ver__?\s*=\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"(?im)^\s*__?ver__?\s*=\s*\(([^)]+)\)"),
    re.compile(r"(?im)^\s*version\s*=\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"(?im)^\s*version\s*=\s*\(([^)]+)\)"),
    re.compile(r"(?im)^\s*ver\s*=\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"(?im)^\s*ver\s*=\s*\(([^)]+)\)"),
]


def _normalize_tuple_version(raw: str) -> Optional[str]:
    parts = [item.strip().strip("'\"") for item in raw.split(",")]
    parts = [item for item in parts if item]
    if not parts:
        return None
    return ".".join(parts)


def read_version(path: Path) -> str:
    """读取版本号，支持多种版本写法。

    :param path: file path for version parsing.
    :return: parsed version string.
    :raises ValueError: when no version info found.
    """
    content = path.read_text(encoding="utf-8")
    for pattern in _VERSION_PATTERNS:
        match = pattern.search(content)
        if not match:
            continue
        value = match.group(1).strip()
        if pattern.pattern.endswith(r"\(([^)]+)\)"):
            normalized = _normalize_tuple_version(value)
            if normalized:
                return normalized
            continue
        if value:
            return value
    raise ValueError(f"Version not found in {path}")
