# buildkit

buildkit 是一套 `setup.py` 时代的构建工具集，重点提供 `--old` / `--release` 模式与可复用的命令类。

## 目标
- 构建逻辑可复用：多项目共享一致的 `setup.py` 行为。
- 发布包隐藏 `.py/.c` 源文件，保持输出目录清晰。
- 继续使用 `setup.py`，避免纯 `pyproject.toml` 的动态限制。

## 快速开始
- 开发安装：`python -m pip install -e .`
- 构建 wheel：`python -m build --wheel`
- 生成 setup 模板：`python -m buildkit init`
- 别名命令：`python -m buildkit setup`

## 构建标志
`--old` / `--release` / `--dry-run` 是构建标志，不是命令，需要搭配 `setup.py` 命令使用。

示例：
- `python setup.py build --old`
- `python setup.py bdist_wheel --release`
- `python setup.py bdist_wheel --dry-run`

## setup.py 示例（简化）
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

## 常见问题
Q: `packages=["mypkg", "mypkg.*"]` 可以吗？  
A: 支持。buildkit 会展开通配包名，排除可用 `exclude_packages`。

Q: 命名空间包（无 `__init__.py`）怎么办？  
A: 使用 `options.use_namespace_packages = True`。

Q: 不加 `--release` 会怎样？  
A: 不删除 `.py`，保留源码。

Q: `--dry-run` 有什么作用？  
A: 预览清理与模块过滤日志，不删除文件。

Q: 环境变量支持哪些？  
A: `BUILDKIT_DRY_RUN=1`、`BUILDKIT_RELEASE=1`、`BUILDKIT_OLD=1`。  
CLI 优先级更高；`--old` 覆盖 `--release` 与 `--dry-run`。

Q: `--release` 下 `.py` 为什么仍会进 whl？  
A: `build_py` 会在 `build_ext` 后复制 `.py`。buildkit 通过 `ReleaseBuildPy` 再次清理。

Q: 如何排除单个模块文件（如 `pipeline.py`）？  
A: 使用 `options.exclude_modules`，在 `build_py` 阶段过滤。

Q: `python setup.py develop` 为什么不清理源码？  
A: `develop` 是源码链接安装，不执行 release 清理。buildkit 会给出提示。

Q: 临时目录构建默认开启吗？  
A: 默认关闭；设置 `USE_TEMP_BUILD=1` 开启。目录默认为 `.build_package_tmp`，可用 `BUILD_TEMP_DIR` 覆盖。

## 模块概览
- `buildkit/commands.py`: `ReleaseBuild`、`ReleaseBuildPy`、`CleanBuild`、`DevelopBuild`
- `buildkit/cython.py`: 源发现与 Cython 编译
- `buildkit/options.py`: 统一构建配置
- `buildkit/flags.py`: 解析 `--old` / `--release` / `--dry-run`
- `buildkit/release.py`: 发布模式源码剥离
- `buildkit/plan.py`: BuildPlan 构建流程编排

## 更多示例
- `docs/examples/README.md`
- `docs/reference-cases.md`

## TODO
- 支持“目录/路径级 keep 规则”（如 `keep_module_globs`）：
  在 `--release` 下允许某些 `.py` 保留在 whl 且不参与 Cython，替代当前仅按文件名 `keep_files` 的能力。
