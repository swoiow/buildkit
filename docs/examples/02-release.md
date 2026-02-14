# Example 02: Release Mode / 发布模式

> 增加自定义 ReleaseBuild，保留指定文件。
> Add a custom ReleaseBuild to keep specific files.

```python
from buildkit.commands import ReleaseBuild
from buildkit.options import default_build_options
from buildkit.plan import BuildPlan
from setuptools import setup


options = default_build_options()


class BuildExt(ReleaseBuild):
    options = options
    keep_files = {"__init__.py", "pkg_info.py", "version.py"}


plan = BuildPlan(
    options=options,
    packages=["litex", "litex.core"],
    package_dir={"litex": "litex"},
)

setup_kwargs, ext_modules = plan.build()
setup_kwargs["cmdclass"] = plan.cmdclass(build_ext_cls=BuildExt)

setup(
    name="litex",
    ext_modules=ext_modules,
    **setup_kwargs,
)
```
