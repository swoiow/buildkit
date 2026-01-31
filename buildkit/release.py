from pathlib import Path
from typing import List, Set


def _should_skip(path: Path, skip_dirs: Set[str]) -> bool:
    return any(part in skip_dirs for part in path.parts)


def strip_sources(
    base_dir: Path,
    patterns: List[str],
    keep_files: Set[str],
    skip_dirs: Set[str],
) -> int:
    """删除指定目录下的源码文件。

    :param base_dir: base directory to scan.
    :param patterns: glob patterns to remove.
    :param keep_files: file names to keep.
    :param skip_dirs: directory names to skip.
    :return: number of removed files.
    """
    removed = 0
    for pattern in patterns:
        for path in base_dir.rglob(pattern):
            if _should_skip(path, skip_dirs):
                continue
            if path.name in keep_files:
                continue
            try:
                path.unlink()
                removed += 1
                print(f"[CLEAN] Removed {path}")
            except OSError as exc:
                print(f"[WARN] Failed to remove {path}: {exc}")
    return removed


def strip_build_output(
    build_lib: Path,
    patterns: List[str],
    keep_files: Set[str],
    skip_dirs: Set[str],
) -> int:
    """清理 build 输出目录中的源码文件。

    :param build_lib: build output directory.
    :param patterns: glob patterns to remove.
    :param keep_files: file names to keep.
    :param skip_dirs: directory names to skip.
    :return: number of removed files.
    """
    if not build_lib.exists():
        return 0
    return strip_sources(build_lib, patterns, keep_files, skip_dirs)
