import os
import platform
import shutil
import tempfile
from contextlib import contextmanager
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


TEMP_BUILD_DIR = os.environ.get("BUILD_TEMP_DIR", ".build_package_tmp")
USE_TEMP_BUILD = os.environ.get("USE_TEMP_BUILD", "0") == "1"


def print_summary(
    package_list: List[str],
    ext_list: List = None,
    exclude_files: List[str] = None,
):
    """打印构建摘要信息，展示平台、包数、扩展模块数、是否启用临时构建目录等。"""
    print("📦 Build Summary")
    print(" ├─ OS:", platform.system(), "/", platform.platform())
    print(" ├─ Python:", platform.python_version())
    print(f" ├─ Packages: {len(package_list)}")
    print(f" ├─ Extensions: {len(ext_list or [])}")
    print(f" ├─ Files excluded: {len(exclude_files or [])}")
    print(" ├─ Temp Build Dir:", "ENABLED" if USE_TEMP_BUILD else "DISABLED")
    print(f" └─ DEBUG: {os.environ.get('DEBUG', '0')}")


def _match_exclude(rel_path: Path, patterns: Sequence[str]) -> bool:
    if not patterns:
        return False

    rel_posix = rel_path.as_posix()
    name = rel_path.name
    return any(
        fnmatchcase(rel_posix, pattern) or fnmatchcase(name, pattern)
        for pattern in patterns
    )


def filter_files(files: Iterable[Path], patterns: Sequence[str]) -> Iterator[Path]:
    """Yield files that do not match any of the provided exclude patterns."""

    if not patterns:
        for file_path in files:
            yield Path(file_path)
        return

    cwd = Path.cwd()
    for file_path in files:
        path_obj = Path(file_path)
        try:
            rel_path = path_obj.relative_to(cwd)
        except ValueError:
            rel_path = path_obj
        if not _match_exclude(rel_path, patterns):
            yield path_obj


def _copy_package_tree(
    src_path: Path,
    dst_path: Path,
    exclude_patterns: Sequence[str],
):
    """Copy a package directory tree while respecting exclusion patterns."""

    def _ignore(src: str, names: List[str]) -> List[str]:
        if not exclude_patterns:
            return []
        src_path_obj = Path(src)
        rel_dir = src_path_obj.relative_to(src_path)
        ignored = []
        for name in names:
            rel_path = rel_dir / name if rel_dir != Path(".") else Path(name)
            if _match_exclude(rel_path, exclude_patterns):
                ignored.append(name)
        return ignored

    shutil.copytree(
        src_path,
        dst_path,
        dirs_exist_ok=True,  # allows merging into existing target
        ignore=_ignore if exclude_patterns else None,
    )


def copy_to_temp_build_dir(
    package_list: List[str],
    base: str = ".",
    target: str = TEMP_BUILD_DIR,
    exclude_patterns: Optional[Sequence[str]] = None,
) -> str:
    """
    将要打包的 packages 拷贝到临时目录中，便于干净构建。
    """
    tmp_dir = Path(target)
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    exclude_patterns = exclude_patterns or []

    for pkg in package_list:
        rel_path = pkg.replace(".", "/")
        src_path = Path(base) / rel_path
        dst_path = tmp_dir / rel_path
        if src_path.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            _copy_package_tree(src_path, dst_path, exclude_patterns)

    print(f"📂 Copied source files to temporary dir: {tmp_dir}")
    return str(tmp_dir)


def get_package_dir_mapping(packages: List[str], tmp_dir: str = TEMP_BUILD_DIR) -> Dict[str, str]:
    """
    为 setup(package_dir=...) 自动生成映射关系。
    """
    mapping = {}
    for pkg in packages:
        top_pkg = pkg.split(".")[0]
        if top_pkg not in mapping:
            mapping[top_pkg] = str(Path(tmp_dir) / top_pkg)
    return mapping


@contextmanager
def temp_build_workspace(
    package_list: List[str],
    base: str = ".",
    target: Optional[str] = None,
    exclude_patterns: Optional[Sequence[str]] = None,
    cleanup: Optional[bool] = None,
) -> Iterator[Tuple[str, Dict[str, str]]]:
    """
    构建临时目录上下文，复制源码并在退出时自动清理。
    返回值为 (tmp_dir, package_dir_mapping)。
    """

    auto_dir = target is None
    if auto_dir:
        target = tempfile.mkdtemp(prefix="buildkit-")

    should_cleanup = cleanup if cleanup is not None else auto_dir

    tmp_dir = copy_to_temp_build_dir(
        package_list,
        base=base,
        target=target,
        exclude_patterns=exclude_patterns,
    )

    try:
        mapping = get_package_dir_mapping(package_list, tmp_dir)
        yield tmp_dir, mapping
    finally:
        if should_cleanup:
            shutil.rmtree(tmp_dir, ignore_errors=True)
