# Setup.py Examples / setup.py 示例

> 本文提供分情况示例，便于从旧接口平滑迁移到新 buildkit API。
> This document provides scenario-based examples for migrating to the new buildkit API.

## Example 1: Minimal Replacement / 最小替换
适用于原本使用 `find_cython_extensions_for_packages` 的项目。
Use when you previously relied on `find_cython_extensions_for_packages`.

```python
from buildkit.cython import extensions_from_packages, safe_cythonize
from buildkit.options import default_build_options
from setuptools import setup

options = default_build_options()

packages = ["litex", "litex.core"]
package_dir = {"litex": "litex"}

ext_modules = []
if not options.flags.is_old:
    exts = extensions_from_packages(packages, package_dir, exclude_init=True)
    ext_modules = safe_cythonize(exts, {"language_level": "3"})

setup(
    name="litex",
    packages=packages,
    package_dir=package_dir,
    ext_modules=ext_modules,
)
```

## Example 2: Incremental Cython / 增量编译
只编译变更的 `.py`，减少构建耗时。
Compile only changed `.py` sources to reduce build time.

```python
from buildkit.cython import (
    discover_sources_from_packages,
    extensions_from_sources,
    filter_changed_sources,
    safe_cythonize,
)
from buildkit.options import default_build_options
from setuptools import setup

options = default_build_options()

packages = ["litex", "litex.core"]
package_dir = {"litex": "litex"}

ext_modules = []
if not options.flags.is_old:
    sources = discover_sources_from_packages(packages, package_dir, exclude_init=True)
    if options.cython_incremental:
        sources = filter_changed_sources(sources, options.cy_cache_file)
    exts = extensions_from_sources(sources, base_dir=options.base_dir)
    ext_modules = safe_cythonize(exts, options.cython_directives)

setup(
    name="litex",
    packages=packages,
    package_dir=package_dir,
    ext_modules=ext_modules,
)
```

## Example 3: Release Mode (Strip Sources) / 发布模式（剥离源码）
发布模式 `--release` 会剥离 `.py/.c`，保留必要入口文件。
Release mode `--release` strips `.py/.c`, keeping essential entry files.

```python
from buildkit.commands import CleanBuild, ReleaseBuild
from buildkit.cython import extensions_from_packages, safe_cythonize
from buildkit.options import default_build_options
from setuptools import setup

options = default_build_options()

packages = ["litex", "litex.core"]
package_dir = {"litex": "litex"}

ext_modules = []
if not options.flags.is_old:
    exts = extensions_from_packages(packages, package_dir, exclude_init=True)
    ext_modules = safe_cythonize(exts, options.cython_directives)

class BuildExt(ReleaseBuild):
    options = options
    keep_files = {"__init__.py", "version.py"}

setup(
    name="litex",
    packages=packages,
    package_dir=package_dir,
    cmdclass={"build_ext": BuildExt, "clean": CleanBuild},
    ext_modules=ext_modules,
)
```

## Example 4: Old Mode Only / 仅旧模式
当只需要源码安装、不做编译时，`--old` 会跳过 Cython。
When `--old` is used, Cython compilation is skipped.

```python
from setuptools import setup

setup(
    name="litex",
    packages=["litex"],
    cmdclass={},
    ext_modules=[],
)
```
