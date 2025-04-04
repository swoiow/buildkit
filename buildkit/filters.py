from fnmatch import fnmatchcase
from typing import List


def filter_packages(packages: List[str], exclude_patterns: List[str]) -> List[str]:
    """
    过滤掉包含或匹配指定模式的包名。
    """
    return [
        pkg for pkg in packages
        if not any(pat in pkg or fnmatchcase(pkg, pat) for pat in exclude_patterns)
    ]


def make_fnmatch_filter(file_names: List[str]) -> List[str]:
    """
    生成用于 fnmatch 的文件匹配模式（如 */model.py）
    """
    return [f"*/{name}" for name in file_names]
