# Buildkit

Buildkit 是一个围绕 `setuptools` 的轻量级构建工具包，帮助你在构建 Python 包或 Cython 扩展时更好地控制流程。它提供了一组可直接复用的命令类与实用工具，适合在自定义的 `setup.py`/`pyproject` 项目中快速集成。

## ✨ 功能概览

- **构建摘要**：通过 `buildkit.summary.print_summary` 输出构建环境、包数量、扩展模块等关键信息，方便在 CI 中快速排查问题。
- **临时构建目录**：`buildkit.summary.copy_to_temp_build_dir` 可以把源码复制到干净的临时目录中，避免脏文件影响打包结果，同时支持 `BUILD_TEMP_DIR`、`USE_TEMP_BUILD` 环境变量控制行为。
- **Package 过滤**：`buildkit.build.FilterBuildPy` 对 `build_py` 命令扩展，允许使用通配模式排除不想被打包的源文件（如测试用例、临时脚本）。
- **智能扩展构建**：`buildkit.build.SmartBuildExt` 和 `buildkit.build_ext.BuildExtCommand` 会在扩展编译完成后自动把生成的二进制复制到项目或 `dist/` 目录，省去手动移动文件的麻烦。
- **包收集工具**：`buildkit.utils.collect_packages` 对 `setuptools.find_packages` 做了简单封装，方便统一管理包收集逻辑。

## 🚀 安装

```bash
pip install buildkit
```

或在你的项目中以子模块 / 直接复制源码的方式引入。

## 🛠️ 在 setup.py 中使用

下面演示如何在传统的 `setup.py` 项目中集成 Buildkit：

```python
import os

from setuptools import setup

from buildkit.build import FilterBuildPy, SmartBuildExt
from buildkit.summary import (
    copy_to_temp_build_dir,
    print_summary,
    get_package_dir_mapping,
)
from buildkit.utils import collect_packages

packages = collect_packages(exclude=["tests", "examples"])
print_summary(packages)

if os.environ.get("USE_TEMP_BUILD") == "1":
    tmp_dir = copy_to_temp_build_dir(packages)
    package_dir = get_package_dir_mapping(packages, tmp_dir)
else:
    package_dir = None

setup(
    name="your-package",
    packages=packages,
    package_dir=package_dir,
    cmdclass={
        "build_py": FilterBuildPy(exclude_files=["*tests.py", "*_dev.py"]),
        "build_ext": SmartBuildExt,
    },
)
```

### 常用环境变量

| 环境变量         | 默认值              | 作用说明 |
|------------------|---------------------|----------|
| `USE_TEMP_BUILD` | `0`                 | 设置为 `1` 时启用临时目录构建。 |
| `BUILD_TEMP_DIR` | `.build_package_tmp`| 指定临时构建目录位置。 |
| `DEBUG`          | `0`                 | 会在构建摘要中展示，方便自定义调试。 |

## 📦 构建流程建议

1. **准备包列表**：使用 `collect_packages` 或手动指定。
2. **打印摘要**：在构建开始时调用 `print_summary`，快速了解当前环境。
3. **可选临时目录**：在需要保持构建目录干净时使用 `copy_to_temp_build_dir`。
4. **自定义命令**：将 `FilterBuildPy`、`SmartBuildExt` 或 `BuildExtCommand` 注入到 `cmdclass` 中，获得更强大的扩展构建体验。
5. **发布**：按需结合 `wheel`、`twine` 等工具发布产物。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request，补充更多构建场景支持。如果你在项目中使用了 Buildkit，也欢迎分享经验或改进建议。

## 📄 许可证

本项目采用 MIT License 许可。
