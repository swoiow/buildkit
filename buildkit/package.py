from fnmatch import fnmatchcase
from typing import Iterable, List


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
