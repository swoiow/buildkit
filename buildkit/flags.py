import sys
from dataclasses import dataclass
from typing import List, Optional

from .runtime import is_old_env, is_release_env, set_dry_run, set_old, set_release


@dataclass(frozen=True)
class BuildFlags:
    """构建标志解析结果。

    :param is_old: install without cythonize and without release stripping.
    :param is_release: enable release stripping after build.
    :param is_dry_run: enable dry-run for release stripping.
    """

    is_old: bool = False
    is_release: bool = False
    is_dry_run: bool = False

    @classmethod
    def from_argv(cls, argv: List[str]) -> "BuildFlags":
        """从 argv 解析构建标志。

        :param argv: argv list.
        :return: BuildFlags instance.
        """
        is_old = is_old_env()
        is_release = is_release_env()
        is_dry_run = is_dry_run()
        if "--old" in argv:
            is_old = True
        if "--release" in argv:
            is_release = True
        if "--dry-run" in argv:
            is_dry_run = True
            is_release = True
        if is_old:
            is_release = False
            is_dry_run = False
        return cls(is_old=is_old, is_release=is_release, is_dry_run=is_dry_run)


def consume_build_flags(argv: Optional[List[str]] = None) -> BuildFlags:
    """解析并移除 argv 中的构建标志。

    :param argv: argv list; defaults to sys.argv and mutates it in place.
    :return: BuildFlags instance.
    """
    target = sys.argv if argv is None else argv
    flags = BuildFlags.from_argv(target)
    set_old(flags.is_old)
    set_release(flags.is_release)
    set_dry_run(flags.is_dry_run)
    for flag in ("--old", "--release", "--dry-run"):
        if flag in target:
            target.remove(flag)
    return flags
