# Example 01: Minimal BuildPlan / 最小化 BuildPlan

> 最简单的 BuildPlan 用法，适合快速迁移。
> Minimal BuildPlan usage for quick migration.

```python
from buildkit.options import default_build_options
from buildkit.plan import BuildPlan
from setuptools import setup


options = default_build_options()

plan = BuildPlan(
    options=options,
    packages=["litex", "litex.core"],
    package_dir={"litex": "litex"},
)

setup_kwargs, ext_modules = plan.build()

setup(
    name="litex",
    ext_modules=ext_modules,
    **setup_kwargs,
)
```
