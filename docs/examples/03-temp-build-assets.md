# Example 03: Temp Build + Assets / 临时目录 + 静态资源

> 在临时目录构建时复制静态资源，避免丢失 icon/js/html。
> Copy assets into the temp build dir to keep icon/js/html available.

```python
from pathlib import Path
import shutil

from buildkit.options import default_build_options
from buildkit.plan import BuildPlan
from setuptools import setup


options = default_build_options()
options.use_temp_build = True

ASSET_DIRS = ["static", "templates", "icons"]


def copy_assets(plan: BuildPlan) -> None:
    src_root = plan.options.base_dir
    dst_root = plan.build_root
    for rel in ASSET_DIRS:
        src = src_root / rel
        dst = dst_root / rel
        if not src.exists():
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


plan = BuildPlan(
    options=options,
    packages=["litex", "litex.core"],
    package_dir={"litex": "litex"},
    asset_copy_hook=copy_assets,
)

setup_kwargs, ext_modules = plan.build()

setup(
    name="litex",
    ext_modules=ext_modules,
    **setup_kwargs,
)
```
