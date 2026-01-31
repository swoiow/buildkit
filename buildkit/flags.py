import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class BuildFlags:
    """构建标志解析结果。

    :param is_old: install without cythonize and without release stripping.
    :param is_release: enable release stripping after build.
    """

    is_old: bool = False
    is_release: bool = False

    @classmethod
    def from_argv(cls, argv: List[str]) -> "BuildFlags":
        """从 argv 解析构建标志。

        :param argv: argv list.
        :return: BuildFlags instance.
        """
        is_old = "--old" in argv
        is_release = "--release" in argv
        if is_old:
            is_release = False
        return cls(is_old=is_old, is_release=is_release)


def consume_build_flags(argv: Optional[List[str]] = None) -> BuildFlags:
    """解析并移除 argv 中的构建标志。

    :param argv: argv list; defaults to sys.argv and mutates it in place.
    :return: BuildFlags instance.
    """
    target = sys.argv if argv is None else argv
    flags = BuildFlags.from_argv(target)
    for flag in ("--old", "--release"):
        if flag in target:
            target.remove(flag)
    return flags
