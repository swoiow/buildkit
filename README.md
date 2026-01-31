# buildkit

buildkit 是一套 `setup.py` 时代的构建工具集，重点提供 `--old` / `--release` 模式与可复用的命令类。
buildkit is a `setup.py`-era build toolkit focused on `--old` / `--release` modes and reusable command classes.

## Goals / 目标
- 构建逻辑可复用：多项目共享一致的 `setup.py` 行为。
  - Reusable build logic across projects with consistent `setup.py` behavior.
- 发布包隐藏 `.py/.c` 源文件，保持输出目录清晰。
  - Hide `.py/.c` sources in release builds for clean outputs.
- 继续使用 `setup.py`，避免纯 `pyproject.toml` 的动态限制。
  - Keep `setup.py` for dynamic logic instead of a pure `pyproject.toml`.

## Quick Start / 快速开始
- 开发安装：`python -m pip install -e .`
  - Editable install: `python -m pip install -e .`
- 构建 wheel：`python -m build --wheel`
  - Build a wheel: `python -m build --wheel`

## Setup.py Example / setup.py 示例
下面示例展示 `--old` / `--release` 的统一入口（简化版）：
The example below shows a unified entry for `--old` / `--release` (simplified):

```python
from pathlib import Path

from buildkit.commands import CleanBuild, ReleaseBuild
from buildkit.cython import extensions_from_sources, filter_changed_sources, safe_cythonize
from buildkit.options import default_build_options
from setuptools import setup

options = default_build_options()

packages = ["yourpkg", "yourpkg.core"]
package_dir = {"yourpkg": "yourpkg"}

ext_modules = []
if not options.flags.is_old:
    sources = [Path("yourpkg/core/tool.py")]
    if options.cython_incremental:
        sources = filter_changed_sources(sources, options.cy_cache_file)
    ext_modules = safe_cythonize(
        extensions_from_sources(sources, base_dir=options.base_dir),
        options.cython_directives,
    )

class BuildExt(ReleaseBuild):
    options = options
    keep_files = {"__init__.py", "version.py"}

setup(
    name="yourpkg",
    cmdclass={"build_ext": BuildExt, "clean": CleanBuild},
    ext_modules=ext_modules,
    packages=packages,
    package_dir=package_dir,
)
```

## Modules / 模块概览
- `buildkit/commands.py`: `ReleaseBuild` 与 `CleanBuild`。
  - `ReleaseBuild` and `CleanBuild`.
- `buildkit/cython.py`: 源发现与 Cython 编译。
  - Source discovery and Cython compilation.
- `buildkit/options.py`: 统一构建配置。
  - Central build options.
- `buildkit/flags.py`: 解析 `--old` / `--release`。
  - Parses `--old` / `--release`.
- `buildkit/release.py`: 发布模式源码剥离。
  - Release-mode source stripping.

## Why setup.py / 为何保留 setup.py
`setup.py` 能承载条件编译与发布模式清理，适合构建逻辑复杂的项目。
`setup.py` handles conditional builds and release cleanup, which suits complex build logic.

## More Examples / 更多示例
详细场景请见 `docs/setup-examples.md`。
See `docs/setup-examples.md` for more scenarios.
