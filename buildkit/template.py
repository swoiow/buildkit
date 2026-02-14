__doc__ = """# Buildkit setup template.
# 该模板展示完整能力，包含可选项与关键注释，用户可按需删减。
# This template shows full capabilities with key comments. Trim as needed.

from pathlib import Path
import shutil

from buildkit.commands import ReleaseBuild
from buildkit.options import default_build_options
from buildkit.plan import BuildPlan
from setuptools import setup

# 解析 --old / --release
options = default_build_options()

# 可选：启用临时目录构建，避免删除本地源码
# options.use_temp_build = True

# 可选：排除某些包或源文件
# options.exclude_package_patterns = ["tests", "examples*"]
# options.exclude_source_globs = ["**/migrations/*.py", "**/legacy/*.py"]
# options.exclude_source_dirs = ["node_modules", "dist"]
# options.use_gitignore = True  # 使用 .gitignore 过滤临时目录复制

# 可选：使用高级 Cython 编译参数
# from buildkit.cython import CYTHON_DIRECTIVES_FULL
# options.cython_directives = dict(CYTHON_DIRECTIVES_FULL)

# 可选：自定义 ReleaseBuild（保留关键文件）
class BuildExt(ReleaseBuild):
    options = options
    keep_files = {"__init__.py", "pkg_info.py", "version.py"}


# 可选：临时目录构建时复制静态资源
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
    packages=["yourpkg", "yourpkg.core"],
    package_dir={"yourpkg": "yourpkg"},
    # exclude_packages=["yourpkg.experimental"],
    # exclude_source_globs=["**/tmp/*.py"],
    # exclude_source_dirs=["tmp"],
    asset_copy_hook=copy_assets,
)

setup_kwargs, ext_modules = plan.build()
setup_kwargs["cmdclass"] = plan.cmdclass(build_ext_cls=BuildExt)

setup(
    name="yourpkg",
    ext_modules=ext_modules,
    **setup_kwargs,
)
"""

from pathlib import Path


TEMPLATE_FILENAME = "buildkit-setup.py"


def render_template() -> str:
    """生成 buildkit setup 模板内容。

    :return: template content.
    """
    return __doc__ or ""


def write_template(target_dir: Path) -> Path:
    """写入 buildkit setup 模板。

    :param target_dir: target directory.
    :return: written file path.
    """
    target_path = target_dir / TEMPLATE_FILENAME
    target_path.write_text(render_template(), encoding="utf-8")
    return target_path
