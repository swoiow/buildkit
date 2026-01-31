import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from Cython.Compiler.Errors import CompileError
from setuptools import Extension


CYTHON_DIRECTIVES_SIMPLE: Dict[str, object] = {
    "language_level": "3",
}

CYTHON_DIRECTIVES_FULL: Dict[str, object] = {
    "language_level": "3",
    "binding": False,
    "boundscheck": False,
    "wraparound": False,
    "initializedcheck": False,
    "cdivision": True,
    "infer_types": True,
    "nonecheck": False,
    "profile": False,
    "linetrace": False,
    "emit_code_comments": False,
    "optimize.use_switch": True,
    "optimize.unpack_method_calls": True,
}


def _ensure_cythonize():
    try:
        from Cython.Build import cythonize
    except ImportError as exc:
        raise RuntimeError("Cython is required for release builds; install it or use --old.") from exc
    return cythonize


def discover_sources_from_packages(
    packages: List[str],
    package_dir: Dict[str, str],
    exclude_init: bool = True,
) -> List[Path]:
    """从包列表中发现 .py 源文件。

    :param packages: package names.
    :param package_dir: mapping from top package to path.
    :param exclude_init: whether to exclude __init__.py.
    :return: list of source paths.
    """
    sources: List[Path] = []
    for pkg in packages:
        parts = pkg.split(".")
        top_pkg = parts[0]
        base = package_dir.get(top_pkg, top_pkg)
        pkg_dir = Path(base, *parts[1:])
        if not pkg_dir.exists():
            continue
        for py_file in pkg_dir.rglob("*.py"):
            if exclude_init and py_file.name == "__init__.py":
                continue
            sources.append(py_file)
    return sources


def extensions_from_sources(sources: Iterable[Path], base_dir: Optional[Path] = None) -> List[Extension]:
    """从源文件路径生成 Extension 列表。

    :param sources: source paths.
    :param base_dir: base dir for module naming; defaults to cwd.
    :return: list of Extension.
    """
    root = base_dir or Path.cwd()
    extensions: List[Extension] = []
    for src in sources:
        try:
            rel = src.resolve().relative_to(root.resolve()).with_suffix("")
        except ValueError as exc:
            raise ValueError(f"Source {src} is not under base_dir {root}. Set base_dir explicitly.") from exc
        mod_name = ".".join(rel.parts)
        extensions.append(Extension(mod_name, [str(src)]))
    return extensions


def extensions_from_packages(
    packages: List[str],
    package_dir: Dict[str, str],
    exclude_init: bool = True,
) -> List[Extension]:
    """从包列表直接生成 Extension。

    :param packages: package names.
    :param package_dir: mapping from top package to path.
    :param exclude_init: whether to exclude __init__.py.
    :return: list of Extension.
    """
    sources = discover_sources_from_packages(packages, package_dir, exclude_init=exclude_init)
    return extensions_from_sources(sources, base_dir=Path.cwd())


def safe_cythonize(extensions: List[Extension], compiler_directives: Dict[str, object]) -> List[Extension]:
    """安全执行 cythonize，失败模块将跳过。

    :param extensions: extension list.
    :param compiler_directives: cython directives.
    :return: compiled extensions.
    """
    cythonize = _ensure_cythonize()
    compiled: List[Extension] = []
    for ext in extensions:
        try:
            compiled.extend(cythonize([ext], compiler_directives=compiler_directives))
        except CompileError as exc:
            print(f"[ERROR] Error compiling {ext.name}: {exc}. Skipping.")
        except Exception as exc:
            print(f"[ERROR] Unexpected error in {ext.name}: {exc}. Skipping.")
    return compiled


def cythonize_extensions(
    extensions: List[Extension],
    compiler_directives: Dict[str, object],
    annotate: bool = False,
) -> List[Extension]:
    """执行 cythonize 并返回编译结果。

    :param extensions: extension list.
    :param compiler_directives: cython directives.
    :param annotate: whether to emit annotation html.
    :return: compiled extensions.
    """
    cythonize = _ensure_cythonize()
    return cythonize(extensions, compiler_directives=compiler_directives, annotate=annotate)


def _load_cache(cache_file: Path) -> Dict[str, float]:
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return {}


def _save_cache(cache_file: Path, cache: Dict[str, float]) -> None:
    cache_file.write_text(json.dumps(cache, indent=2))


def filter_changed_sources(
    sources: Iterable[Path],
    cache_file: Path,
    force: bool = False,
) -> List[Path]:
    """根据 mtime 缓存过滤变更源文件。

    :param sources: source paths.
    :param cache_file: cache file path.
    :param force: rebuild all sources.
    :return: changed source paths.
    """
    if force:
        return [src for src in sources if src.exists()]

    old_cache = _load_cache(cache_file)
    new_cache: Dict[str, float] = {}
    changed: List[Path] = []

    for src in sources:
        if not src.exists():
            continue
        mtime = src.stat().st_mtime
        key = str(src)
        new_cache[key] = mtime
        if old_cache.get(key) != mtime:
            changed.append(src)

    _save_cache(cache_file, new_cache)
    return changed
