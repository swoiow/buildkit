from pathlib import Path
from typing import List, Optional, Set

from setuptools import Command
from setuptools.command.build_ext import build_ext

from .options import BuildOptions, default_build_options
from .release import strip_build_output, strip_sources
from .summary import print_summary


class ReleaseBuild(build_ext):
    """发布构建：编译扩展后清理源码文件。

    :param options: BuildOptions instance.
    """

    options: Optional[BuildOptions] = None
    keep_files: Set[str] = set()
    strip_patterns: List[str] = []
    skip_dirs: Set[str] = set()

    def _effective_options(self) -> BuildOptions:
        base = self.options or default_build_options()
        return base.merged_with_overrides(
            keep_files=self.keep_files,
            strip_patterns=self.strip_patterns,
            skip_dirs=self.skip_dirs,
        )

    def run(self):
        super().run()
        options = self._effective_options()
        if not options.flags.is_release:
            if options.summary_enabled:
                print_summary(
                    getattr(self, "package_list", []),
                    getattr(self, "extensions", None),
                    options=options,
                )
            return
        removed = strip_sources(
            options.base_dir,
            options.strip_patterns,
            options.keep_files,
            options.skip_dirs,
        )
        build_lib = getattr(self, "build_lib", None)
        if build_lib:
            removed += strip_build_output(
                Path(build_lib),
                options.strip_patterns,
                options.keep_files,
                options.skip_dirs,
            )
        self.post_release_cleanup(removed, options)
        if options.summary_enabled:
            print_summary(
                getattr(self, "package_list", []),
                getattr(self, "extensions", None),
                options=options,
            )

    def post_release_cleanup(self, removed: int, options: BuildOptions) -> None:
        """发布模式后置钩子，供子类覆盖。

        :param removed: number of removed files.
        :param options: build options.
        :return: None.
        """
        print(f"[CLEAN] Removed {removed} source files in release mode")


class CleanBuild(Command):
    """清理构建产物（build、临时目录、扩展文件）。"""

    description = "clean build outputs"
    user_options = []

    options: Optional[BuildOptions] = None
    clean_dirs: List[str] = ["build"]
    clean_patterns: List[str] = ["*.so", "*.pyd", "*.c"]
    skip_dirs: Set[str] = set()

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def _effective_options(self) -> BuildOptions:
        base = self.options or default_build_options()
        return base.merged_with_overrides(skip_dirs=self.skip_dirs)

    def run(self):
        options = self._effective_options()
        base_dir = options.base_dir
        for dir_name in self.clean_dirs:
            target = base_dir / dir_name
            if target.exists():
                for path in sorted(target.rglob("*"), reverse=True):
                    if any(part in options.skip_dirs for part in path.parts):
                        continue
                    try:
                        if path.is_dir():
                            path.rmdir()
                        else:
                            path.unlink()
                    except OSError:
                        pass
                try:
                    target.rmdir()
                except OSError:
                    pass
        if options.use_temp_build:
            temp_dir = base_dir / options.temp_build_dir
            if temp_dir.exists():
                for path in sorted(temp_dir.rglob("*"), reverse=True):
                    try:
                        if path.is_dir():
                            path.rmdir()
                        else:
                            path.unlink()
                    except OSError:
                        pass
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass
        strip_sources(base_dir, self.clean_patterns, options.keep_files, options.skip_dirs)
