import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from .cython import CYTHON_DIRECTIVES_SIMPLE
from .flags import BuildFlags, consume_build_flags


@dataclass
class BuildOptions:
    """构建配置。

    :param flags: build flags.
    :param base_dir: project root for cleanup and discovery.
    :param build_root: build root for release stripping.
    :param keep_files: file names to keep when stripping sources.
    :param strip_patterns: glob patterns to remove in release mode.
    :param skip_dirs: directory names to skip during cleanup.
    :param temp_build_dir: temporary build directory name.
    :param use_temp_build: whether to use temporary build directory.
    :param cython_directives: compiler directives for cythonize.
    :param cython_incremental: enable incremental cythonize.
    :param cy_cache_file: cache file path for incremental builds.
    :param summary_enabled: enable summary output.
    :param exclude_packages: package name patterns to exclude.
    :param exclude_sources: source file glob patterns to exclude.
    :param exclude_modules: module file globs to exclude from build_py output.
    :param exclude_module_globs: legacy alias for exclude_modules.
    :param exclude_package_patterns: legacy alias for exclude_packages.
    :param exclude_source_globs: legacy alias for exclude_sources.
    :param exclude_source_dirs: directory names to exclude from source discovery.
    :param use_gitignore: whether to respect .gitignore when copying to temp build.
    :param gitignore_filename: gitignore file name.
    :param use_namespace_packages: whether to use find_namespace_packages for package expansion.
    """

    flags: BuildFlags
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    build_root: Optional[Path] = None
    keep_files: Set[str] = field(default_factory=lambda: {"__init__.py", "pkg_info.py"})
    strip_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.c"])
    skip_dirs: Set[str] = field(
        default_factory=lambda: {
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            ".idea",
            ".pytest_cache",
        }
    )
    temp_build_dir: str = field(default_factory=lambda: os.environ.get("BUILD_TEMP_DIR", ".build_package_tmp"))
    use_temp_build: bool = field(default_factory=lambda: os.environ.get("USE_TEMP_BUILD", "0") == "1")
    cython_directives: Dict[str, object] = field(default_factory=lambda: dict(CYTHON_DIRECTIVES_SIMPLE))
    cython_incremental: bool = False
    cy_cache_file: Path = field(default_factory=lambda: Path(".cycache"))
    summary_enabled: bool = True
    exclude_packages: List[str] = field(default_factory=list)
    exclude_sources: List[str] = field(default_factory=list)
    exclude_modules: List[str] = field(default_factory=list)
    exclude_module_globs: List[str] = field(default_factory=list)
    exclude_package_patterns: List[str] = field(default_factory=list)
    exclude_source_globs: List[str] = field(default_factory=list)
    exclude_source_dirs: List[str] = field(default_factory=list)
    use_gitignore: bool = False
    gitignore_filename: str = ".gitignore"
    use_namespace_packages: bool = False

    def merged_with_overrides(
        self,
        keep_files: Optional[Set[str]] = None,
        strip_patterns: Optional[List[str]] = None,
        skip_dirs: Optional[Set[str]] = None,
    ) -> "BuildOptions":
        """合并类覆盖配置，生成新的 BuildOptions。

        :param keep_files: extra keep files.
        :param strip_patterns: extra strip patterns.
        :param skip_dirs: extra skip dirs.
        :return: new BuildOptions instance.
        """
        return BuildOptions(
            flags=self.flags,
            base_dir=self.base_dir,
            build_root=self.build_root,
            keep_files=set(self.keep_files) | set(keep_files or set()),
            strip_patterns=list(self.strip_patterns) + list(strip_patterns or []),
            skip_dirs=set(self.skip_dirs) | set(skip_dirs or set()),
            temp_build_dir=self.temp_build_dir,
            use_temp_build=self.use_temp_build,
            cython_directives=dict(self.cython_directives),
            cython_incremental=self.cython_incremental,
            cy_cache_file=self.cy_cache_file,
            summary_enabled=self.summary_enabled,
            exclude_package_patterns=list(self.exclude_package_patterns),
            exclude_source_globs=list(self.exclude_source_globs),
            exclude_source_dirs=list(self.exclude_source_dirs),
            use_gitignore=self.use_gitignore,
            gitignore_filename=self.gitignore_filename,
            use_namespace_packages=self.use_namespace_packages,
            exclude_packages=list(self.exclude_packages),
            exclude_sources=list(self.exclude_sources),
            exclude_modules=list(self.exclude_modules),
            exclude_module_globs=list(self.exclude_module_globs),
        )

    def effective_exclude_packages(self) -> List[str]:
        """获取完整包排除列表。

        :return: package exclude patterns.
        """
        return list(self.exclude_packages) + list(self.exclude_package_patterns)

    def effective_exclude_sources(self) -> List[str]:
        """获取完整源码排除列表。

        :return: source file exclude globs.
        """
        return list(self.exclude_sources) + list(self.exclude_source_globs)

    def effective_exclude_modules(self) -> List[str]:
        """获取完整模块排除列表。

        :return: module file exclude globs.
        """
        return list(self.exclude_modules) + list(self.exclude_module_globs)


def default_build_options(argv: Optional[List[str]] = None, base_dir: Optional[Path] = None) -> BuildOptions:
    """构建默认配置并解析 --old/--release。

    :param argv: argv list; defaults to sys.argv.
    :param base_dir: project base dir; defaults to cwd.
    :return: BuildOptions instance.
    """
    flags = consume_build_flags(argv)
    return BuildOptions(flags=flags, base_dir=base_dir or Path.cwd())
