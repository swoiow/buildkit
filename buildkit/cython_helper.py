import json
import os
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from Cython.Build import cythonize
from Cython.Compiler.Errors import CompileError
from setuptools import Extension


CY_CACHE_FILE = Path(".cycache")


def _normalize_patterns(patterns: Optional[Sequence[str]]) -> List[str]:
    """Normalize and clean an optional sequence of filename patterns.

    Args:
        patterns (Optional[Sequence[str]]): A sequence of pattern strings, possibly containing empty or None values.

    Returns:
        List[str]: The cleaned list of valid patterns.

    Examples:
        >>> _normalize_patterns(["*.py", "", None])
        ['*.py']
    """
    return [p for p in (patterns or []) if p]


def _should_exclude(path: Path, patterns: Sequence[str], root: Optional[Path] = None) -> bool:
    """Determine whether a given path should be excluded based on match patterns.

    Args:
        path (Path): The file path to test.
        patterns (Sequence[str]): List of fnmatch-compatible exclusion patterns.
        root (Optional[Path]): Optional root directory to compute relative paths for matching.

    Returns:
        bool: True if the path matches any exclusion pattern, False otherwise.

    Examples:
        >>> _should_exclude(Path("src/test_temp.py"), ["test_*"])
        True
    """
    if not patterns:
        return False

    candidates = {path.name, path.as_posix()}
    if root:
        try:
            rel = path.relative_to(root)
            candidates.add(rel.as_posix())
        except ValueError:
            pass

    return any(fnmatchcase(candidate, pattern) for candidate in candidates for pattern in patterns)


def _iter_target_files(target: str) -> Iterator[Tuple[Path, Path]]:
    """Iterate through all Python files from a given target path or glob.

    Args:
        target (str): Path, glob pattern, or dotted module path.

    Yields:
        Tuple[Path, Path]: A tuple of (Python file path, root directory).

    Examples:
        >>> list(_iter_target_files("myapp/**/*.py"))[:1]  # doctest: +SKIP
        [(Path('myapp/core/utils.py'), Path('myapp'))]
    """
    path = Path(target)
    target_str = str(target)

    if any(ch in target_str for ch in "*?[]"):
        for match in Path().glob(target_str):
            yield from _iter_resolved_path(match)
        return

    if path.exists():
        yield from _iter_resolved_path(path)
        return

    dotted_candidate = Path(target_str.replace(".", os.sep) + ".py")
    if dotted_candidate.exists():
        yield from _iter_resolved_path(dotted_candidate)


def _iter_resolved_path(path: Path) -> Iterator[Tuple[Path, Path]]:
    """Recursively resolve all Python files under a given path.

    Args:
        path (Path): Directory or file path to resolve.

    Yields:
        Tuple[Path, Path]: Each tuple represents (Python file, root directory).

    Examples:
        >>> list(_iter_resolved_path(Path("mypkg")))[:2]  # doctest: +SKIP
        [(Path('mypkg/__init__.py'), Path('mypkg')), (Path('mypkg/core.py'), Path('mypkg'))]
    """
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
    """Derive a fully-qualified module name from a source file path.

    Args:
        py_file (Path): Path to the Python source file.
        package_dir (Optional[Dict[str, str]]): setuptools-style package mapping, e.g. {"mypkg": "src"}.
        source_roots (Optional[Dict[str, str]]): Optional root directory-to-prefix mapping for Cython projects.

    Returns:
        str: The module import path, e.g. "mypkg.utils.helpers".

    Examples:
        >>> _module_name_from_path(Path("src/mypkg/utils/helpers.py"), {"mypkg": "src"})
        'mypkg.utils.helpers'
    """
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
    """Expand directories, globs, and files into a list of unique Python source files.

    Args:
        targets (Sequence[str]): List of directories, files, or glob patterns.
        exclude_patterns (Optional[Sequence[str]]): List of exclusion patterns.
        exclude_init (bool): Whether to exclude `__init__.py` files.

    Returns:
        List[Path]: Sorted list of unique Python file paths.

    Examples:
        >>> resolve_python_sources(["mypkg"], exclude_patterns=["*_test.py"])  # doctest: +SKIP
        [Path('mypkg/core.py'), Path('mypkg/utils/io.py')]
    """
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
    """Generate a list of Cython Extension objects from given targets.

    Args:
        targets (Sequence[str]): List of Python sources, directories, or module paths.
        package_dir (Optional[Dict[str, str]]): setuptools-style package mapping.
        source_roots (Optional[Dict[str, str]]): Custom root-to-prefix mapping for module names.
        exclude_patterns (Optional[Sequence[str]]): List of exclusion patterns.
        exclude_init (bool): Whether to skip `__init__.py`.

    Returns:
        List[Extension]: A list of setuptools.Extension objects.

    Examples:
        >>> exts = build_extensions_from_targets(["src/mypkg"], {"mypkg": "src"})  # doctest: +SKIP
        >>> [e.name for e in exts]
        ['mypkg.core', 'mypkg.utils']
    """
    py_files = resolve_python_sources(targets, exclude_patterns, exclude_init)
    normalized_roots = {
        str(Path(root).resolve()): prefix for root, prefix in (source_roots or {}).items()
    }

    return [
        Extension(_module_name_from_path(py, package_dir, normalized_roots), [str(py)])
        for py in py_files
    ]


def find_cython_extensions_for_packages(
    packages: Sequence[str],
    package_dir: Dict[str, str],
    exclude_init: bool = True,
    exclude_files: Optional[Sequence[str]] = None,
) -> List[Extension]:
    """Discover all `.py` files within logical Python packages and create Cython extensions.

    This function walks through package directories (as defined by `package_dir`)
    and builds a list of `setuptools.Extension` objects representing the discovered
    Python modules.

    Args:
        packages (Sequence[str]): List of logical package names, e.g. ["etl.commons"].
        package_dir (Dict[str, str]): Mapping from top-level package name to directory path,
            e.g. {"etl": "src"}.
        exclude_init (bool): Whether to exclude `__init__.py` files.
        exclude_files (Optional[Sequence[str]]): Optional list of filename patterns to exclude.

    Returns:
        List[Extension]: A list of Cython extension objects ready for compilation.

    Examples:
        >>> find_cython_extensions_for_packages(["etl.commons"], {"etl": "src"})  # doctest: +SKIP
        [<setuptools.extension.Extension('etl.commons.core', ...)>]
    """
    exclude_files = [p for p in (exclude_files or []) if p]
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
    """Safely execute `cythonize`, skipping modules that fail to compile.

    Args:
        extensions (List[Extension]): List of extensions to compile.
        compiler_directives (dict): Dictionary of Cython compiler directives.

    Returns:
        List[Extension]: List of successfully compiled extensions.

    Examples:
        >>> safe_cythonize(exts, {"language_level": "3"})  # doctest: +SKIP
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
    """Load the modification-time cache from `.cycache` file.

    Returns:
        dict: Mapping of file paths to last modification timestamps.
    """
    return json.loads(CY_CACHE_FILE.read_text()) if CY_CACHE_FILE.exists() else {}


def save_cy_cache(file_mtime_map: dict):
    """Save current file modification times into `.cycache`.

    Args:
        file_mtime_map (dict): Mapping of file paths to modification times.
    """
    CY_CACHE_FILE.write_text(json.dumps(file_mtime_map, indent=2))


def collect_changed_sources(files: Sequence[str]) -> List[str]:
    """Detect which source files have changed since the last build.

    Args:
        files (Sequence[str]): List of source file paths.

    Returns:
        List[str]: List of changed file paths.

    Examples:
        >>> collect_changed_sources(["src/mypkg/core.py", "src/mypkg/utils/io.py"])  # doctest: +SKIP
        ['src/mypkg/core.py']
    """
    old = load_cy_cache()
    new = {}
    changed = []

    for f in files:
        path = Path(f)
        if not path.exists():
            continue
        mtime = path.stat().st_mtime
        new[str(path)] = mtime
        if old.get(str(path)) != mtime:
            changed.append(str(path))

    save_cy_cache(new)
    return changed


def safe_incremental_cythonize(
    extensions: List[Extension],
    compiler_directives: dict,
    force: bool = False,
) -> List[Extension]:
    """Perform incremental Cython builds by recompiling only changed sources.

    Args:
        extensions (List[Extension]): All extension objects to consider.
        compiler_directives (dict): Cython compiler directives.
        force (bool): If True, rebuild all extensions regardless of change state.

    Returns:
        List[Extension]: List of successfully compiled extensions.

    Examples:
        >>> exts = build_extensions_from_targets(["src/mypkg"], {"mypkg": "src"})  # doctest: +SKIP
        >>> safe_incremental_cythonize(exts, {"language_level": "3"})  # doctest: +SKIP
    """
    all_sources = [ext.sources[0] for ext in extensions]
    changed_files = collect_changed_sources(all_sources) if not force else all_sources

    filtered = [ext for ext in extensions if ext.sources[0] in changed_files]
    if not filtered:
        print("✅ No source changes detected. Skipping Cython build.")
        return []

    print(f"⚙️ Detected {len(filtered)} changed source file(s), rebuilding...")
    return safe_cythonize(filtered, compiler_directives)
