import glob
import json
import os
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from Cython.Build import cythonize
from Cython.Compiler.Errors import CompileError
from setuptools import Extension


CY_CACHE_FILE = ".cycache"


def _normalize_patterns(patterns: Optional[Sequence[str]]) -> List[str]:
    return [p for p in (patterns or []) if p]


def _should_exclude(path: Path, patterns: Sequence[str], root: Optional[Path] = None) -> bool:
    if not patterns:
        return False

    candidates = {path.name, path.as_posix()}
    if root is not None:
        try:
            rel = path.relative_to(root)
            candidates.add(rel.as_posix())
        except ValueError:
            pass

    return any(fnmatchcase(candidate, pattern) for candidate in candidates for pattern in patterns)


def _iter_target_files(target: str) -> Iterator[Tuple[Path, Path]]:
    path = Path(target)
    target_str = str(target)
    contains_glob = any(ch in target_str for ch in "*?[]")

    if contains_glob:
        for match in glob.glob(target_str, recursive=True):
            yield from _iter_resolved_path(Path(match))
        return

    if path.exists():
        yield from _iter_resolved_path(path)
        return

    dotted_candidate = Path(target_str.replace(".", os.sep) + ".py")
    if dotted_candidate.exists():
        yield from _iter_resolved_path(dotted_candidate)


def _iter_resolved_path(path: Path) -> Iterator[Tuple[Path, Path]]:
    if path.is_dir():
        for item in path.rglob("*.py"):
            yield item, path
    elif path.is_file() and path.suffix == ".py":
        yield path, path.parent


def _module_name_from_path(
    py_file: Path,
    package_dir: Optional[Dict[str, str]] = None,
    source_roots: Optional[Dict[str, str]] = None,
) -> str:
    package_dir = package_dir or {}
    resolved = py_file.resolve()

    for pkg, src in sorted(package_dir.items(), key=lambda item: len(str(item[1])), reverse=True):
        src_path = Path(src).resolve()
        try:
            rel = resolved.relative_to(src_path)
        except ValueError:
            continue
        module_parts: List[str] = [pkg] if pkg else []
        module_parts.extend(rel.with_suffix("").parts)
        if module_parts and module_parts[-1] == "__init__":
            module_parts.pop()
        return ".".join(part for part in module_parts if part)

    if source_roots:
        for root, prefix in sorted(source_roots.items(), key=lambda item: len(str(item[0])), reverse=True):
            root_path = Path(root).resolve()
            try:
                rel = resolved.relative_to(root_path)
            except ValueError:
                continue
            module_parts = [prefix] if prefix else []
            module_parts.extend(rel.with_suffix("").parts)
            if module_parts and module_parts[-1] == "__init__":
                module_parts.pop()
            return ".".join(part for part in module_parts if part)

    rel = resolved.with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve_python_sources(
    targets: Sequence[str],
    exclude_patterns: Optional[Sequence[str]] = None,
    exclude_init: bool = True,
) -> List[Path]:
    """展开包含目录、文件或通配符的目标列表，生成唯一的 Python 源文件集合。"""

    exclude_patterns = _normalize_patterns(exclude_patterns)
    seen = set()
    files: List[Path] = []

    for target in targets:
        for py_file, root in _iter_target_files(target):
            if exclude_init and py_file.name == "__init__.py":
                continue
            if _should_exclude(py_file, exclude_patterns, root):
                continue
            resolved = py_file.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(resolved)

    return sorted(files)


def build_extensions_from_targets(
    targets: Sequence[str],
    package_dir: Optional[Dict[str, str]] = None,
    source_roots: Optional[Dict[str, str]] = None,
    exclude_patterns: Optional[Sequence[str]] = None,
    exclude_init: bool = True,
) -> List[Extension]:
    """
    根据目标列表（目录、文件、glob 或模块路径）生成 Cython Extension 列表。
    """

    py_files = resolve_python_sources(targets, exclude_patterns, exclude_init)
    extensions: List[Extension] = []
    normalized_roots = {
        str(Path(root).resolve()): prefix for root, prefix in (source_roots or {}).items()
    }

    for py_file in py_files:
        module_name = _module_name_from_path(py_file, package_dir, normalized_roots)
        extensions.append(Extension(module_name, [str(py_file)]))

    return extensions


def find_cython_extensions_for_packages(
    packages: Sequence[str],
    package_dir: Dict[str, str],
    exclude_init: bool = True,
    exclude_files: Optional[Sequence[str]] = None,
) -> List[Extension]:
    """
    查找逻辑包中的 .py 文件，并生成 Cython Extension 对象列表。

    示例:
    >>> find_cython_extensions_for_packages(["etl.commons"], {"etl": "."})
    """

    exclude_files = _normalize_patterns(exclude_files)
    extensions: List[Extension] = []

    for pkg in packages:
        parts = pkg.split(".")
        top_pkg = parts[0]
        base = package_dir.get(top_pkg, top_pkg)
        subdirs = parts[1:]
        pkg_dir = Path(base, *subdirs)
        if not pkg_dir.exists():
            continue
        for py_file in pkg_dir.rglob("*.py"):
            if exclude_init and py_file.name == "__init__.py":
                continue
            if _should_exclude(py_file, exclude_files, pkg_dir):
                continue
            rel_path = py_file.relative_to(pkg_dir).with_suffix("")
            mod_suffix = ".".join(rel_path.parts)
            mod_name = pkg if not mod_suffix else f"{pkg}.{mod_suffix}"
            extensions.append(Extension(mod_name, [str(py_file)]))

    return extensions


def safe_cythonize(extensions: List[Extension], compiler_directives: dict) -> List[Extension]:
    """
    安全执行 Cythonize，失败模块将跳过。

    示例:
    >>> safe_cythonize(exts, {"language_level": "3"})
    """
    good_extensions = []
    for ext in extensions:
        try:
            compiled = cythonize([ext], compiler_directives=compiler_directives)
            good_extensions.extend(compiled)
        except CompileError as e:
            print(f"❌ Error compiling {ext.name}: {e}. Skipping.")
        except Exception as e:
            print(f"❌ Unexpected error in {ext.name}: {e}. Skipping.")
    return good_extensions


def load_cy_cache() -> dict:
    """从缓存文件加载源文件的上次修改时间"""
    if Path(CY_CACHE_FILE).exists():
        return json.loads(Path(CY_CACHE_FILE).read_text())
    return {}


def save_cy_cache(file_mtime_map: dict):
    """保存源文件的当前修改时间到缓存文件"""
    Path(CY_CACHE_FILE).write_text(json.dumps(file_mtime_map, indent=2))


def collect_changed_sources(files: Sequence[str]) -> List[str]:
    """
    根据 .cycache 检测哪些源文件发生变化。

    示例:
    >>> collect_changed_sources(["etl/commons/core.py", "etl/base.py"])
    """
    old = load_cy_cache()
    new = {}
    changed = []

    for f in files:
        f = str(f)
        if not Path(f).exists():
            continue
        mtime = os.path.getmtime(f)
        new[f] = mtime
        if old.get(f) != mtime:
            changed.append(f)

    save_cy_cache(new)
    return changed


def safe_incremental_cythonize(
    extensions: List[Extension],
    compiler_directives: dict,
    force: bool = False
) -> List[Extension]:
    """
    增量方式进行 cythonize，仅构建变更的模块。

    示例:
    >>> safe_incremental_cythonize(exts, {"language_level": "3"})
    """
    all_sources = [ext.sources[0] for ext in extensions]
    changed_files = collect_changed_sources(all_sources) if not force else all_sources

    filtered = [ext for ext in extensions if ext.sources[0] in changed_files]
    if not filtered:
        print("✅ No source changes detected. Skipping Cython build.")
        return []

    print(f"⚙️ Detected {len(filtered)} changed source file(s), rebuilding...")
    return safe_cythonize(filtered, compiler_directives)
