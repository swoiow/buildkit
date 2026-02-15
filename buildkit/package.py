from fnmatch import fnmatchcase
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from setuptools import find_namespace_packages, find_packages


def _is_pattern(value: str) -> bool:
    return any(ch in value for ch in ("*", "?", "[", "]"))


def _normalize_root_dir(base_dir: Path, package_dir: dict, top_pkg: str) -> Path:
    if top_pkg in package_dir:
        return (base_dir / package_dir[top_pkg]).resolve()
    if "" in package_dir:
        return (base_dir / package_dir[""] / top_pkg).resolve()
    return (base_dir / top_pkg).resolve()


def _expand_wildcard(
    pattern: str,
    base_dir: Path,
    package_dir: dict,
    use_namespace_packages: bool,
) -> List[str]:
    top_pkg = pattern.split(".")[0] if "." in pattern else ""
    finder = find_namespace_packages if use_namespace_packages else find_packages
    if top_pkg:
        root_dir = _normalize_root_dir(base_dir, package_dir, top_pkg)
        candidates = finder(where=str(root_dir))
        full_names = [top_pkg] + [f"{top_pkg}.{name}" for name in candidates]
        return [name for name in full_names if fnmatchcase(name, pattern)]
    root_dir = (base_dir / package_dir.get("", ".")).resolve()
    candidates = finder(where=str(root_dir))
    return [name for name in candidates if fnmatchcase(name, pattern)]


def expand_packages(
    packages: Iterable[str],
    package_dir: dict,
    base_dir: Path,
    use_namespace_packages: bool = False,
) -> List[str]:
    """展开通配符包名为实际包列表。

    :param packages: package names or wildcard patterns.
    :param package_dir: mapping from package name to path.
    :param base_dir: project base dir.
    :param use_namespace_packages: whether to use find_namespace_packages.
    :return: expanded package list.
    """
    expanded: List[str] = []
    seen: Set[str] = set()
    for pkg in packages:
        if _is_pattern(pkg):
            found = _expand_wildcard(pkg, base_dir, package_dir, use_namespace_packages)
            for name in found:
                if name in seen:
                    continue
                seen.add(name)
                expanded.append(name)
            continue
        if pkg in seen:
            continue
        seen.add(pkg)
        expanded.append(pkg)
    return expanded


def filter_packages(packages: Iterable[str], exclude_patterns: List[str]) -> List[str]:
    """过滤不需要打包的包名。

    :param packages: package names.
    :param exclude_patterns: patterns or substrings to exclude.
    :return: filtered package list.
    """
    filtered: List[str] = []
    for pkg in packages:
        if any(pat in pkg or fnmatchcase(pkg, pat) for pat in exclude_patterns):
            continue
        filtered.append(pkg)
    return filtered


def split_packages(
    packages: Iterable[str],
    exclude_patterns: List[str],
) -> Tuple[List[str], List[str]]:
    """拆分包列表为保留与排除两组。

    :param packages: package names.
    :param exclude_patterns: patterns or substrings to exclude.
    :return: (included, excluded).
    """
    included: List[str] = []
    excluded: List[str] = []
    for pkg in packages:
        if any(pat in pkg or fnmatchcase(pkg, pat) for pat in exclude_patterns):
            excluded.append(pkg)
            continue
        included.append(pkg)
    return included, excluded


def package_to_path(pkg: str, package_dir: dict, base_dir: Path) -> Path:
    """将包名转换为目录路径。

    :param pkg: package name.
    :param package_dir: mapping from package name to path.
    :param base_dir: project base dir.
    :return: resolved package path.
    """
    parts = pkg.split(".")
    top_pkg = parts[0]
    if top_pkg in package_dir:
        base = base_dir / package_dir[top_pkg]
        return Path(base, *parts[1:]).resolve()
    if "" in package_dir:
        base = base_dir / package_dir[""]
        return Path(base, *parts).resolve()
    return Path(base_dir, *parts).resolve()
