from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Type

from setuptools import Extension

from .commands import CleanBuild, ReleaseBuild
from .cython import (
    discover_sources_from_packages,
    extensions_from_sources,
    filter_changed_sources,
    safe_cythonize,
)
from .options import BuildOptions
from .package import expand_packages, package_to_path, split_packages
from .summary import copy_to_temp_build_dir, get_package_dir_mapping


@dataclass
class BuildPlan:
    """统一构建流程的上下文。

    :param options: build options.
    :param packages: package list.
    :param package_dir: package_dir mapping.
    :param exclude_packages: package exclusion patterns.
    :param exclude_source_globs: source path glob patterns.
    :param exclude_source_dirs: directory names to skip.
    :param asset_copy_hook: optional hook for copying assets into temp build dir.
    """

    options: BuildOptions
    packages: List[str]
    package_dir: Dict[str, str]
    exclude_packages: List[str] = field(default_factory=list)
    exclude_source_globs: List[str] = field(default_factory=list)
    exclude_source_dirs: List[str] = field(default_factory=list)
    asset_copy_hook: Optional[Callable[["BuildPlan"], None]] = None

    effective_packages: List[str] = field(init=False, default_factory=list)
    effective_package_dir: Dict[str, str] = field(init=False, default_factory=dict)
    build_root: Path = field(init=False)
    excluded_packages: List[str] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.build_root = self.options.base_dir
        expanded = expand_packages(
            self.packages,
            self.package_dir,
            self.options.base_dir,
            use_namespace_packages=self.options.use_namespace_packages,
        )
        included, excluded = split_packages(
            expanded,
            self.options.exclude_package_patterns + self.exclude_packages,
        )
        self.effective_packages = included
        self.excluded_packages = excluded
        self.effective_package_dir = dict(self.package_dir)

    def apply_temp_build(self) -> None:
        """复制源码到临时目录并更新 package_dir。"""
        if not self.options.use_temp_build:
            return
        tmp_dir = copy_to_temp_build_dir(
            self.effective_packages,
            base=str(self.options.base_dir),
            target=self.options.temp_build_dir,
            options=self.options,
        )
        self.effective_package_dir = get_package_dir_mapping(self.effective_packages, tmp_dir)
        self.build_root = Path(tmp_dir)
        if self.asset_copy_hook:
            self.asset_copy_hook(self)

    def prepare_extensions(self) -> List[Extension]:
        """构建 Cython 扩展列表。"""
        if self.options.flags.is_old:
            return []
        excluded_dirs = set()
        for pkg in self.excluded_packages:
            path = package_to_path(pkg, self.effective_package_dir, self.build_root)
            try:
                rel = path.relative_to(self.build_root).as_posix()
            except ValueError:
                rel = path.as_posix()
            excluded_dirs.add(rel)
        sources = discover_sources_from_packages(
            self.effective_packages,
            self.effective_package_dir,
            exclude_init=True,
            exclude_globs=self.options.exclude_source_globs + self.exclude_source_globs,
            exclude_dirs=set(self.options.exclude_source_dirs + self.exclude_source_dirs)
                         | set(excluded_dirs),
        )
        if self.options.cython_incremental:
            sources = filter_changed_sources(sources, self.options.cy_cache_file)
        extensions = extensions_from_sources(sources, base_dir=self.build_root)
        return safe_cythonize(extensions, self.options.cython_directives)

    def cmdclass(self, build_ext_cls: Optional[Type[ReleaseBuild]] = None) -> Dict[str, Type[object]]:
        """生成 cmdclass 映射。

        :param build_ext_cls: custom build_ext class.
        :return: cmdclass mapping.
        """
        build_ext_cls = build_ext_cls or ReleaseBuild
        build_ext_cls.options = self.options
        build_ext_cls.package_list = list(self.effective_packages)
        return {"build_ext": build_ext_cls, "clean": CleanBuild}

    def build(self) -> Tuple[Dict[str, object], List[Extension]]:
        """生成 setup.py 所需配置。

        :return: (setup_kwargs, ext_modules)
        """
        self.apply_temp_build()
        ext_modules = self.prepare_extensions()
        setup_kwargs = {
            "packages": list(self.effective_packages),
            "package_dir": dict(self.effective_package_dir),
            "cmdclass": self.cmdclass(),
        }
        return setup_kwargs, ext_modules
