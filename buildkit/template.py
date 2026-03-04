__doc__ = """# Buildkit setup template.
# 该模板展示完整能力，包含可选项与关键注释，用户可按需删减。
# This template shows full capabilities with key comments. Trim as needed.

from pathlib import Path
import shutil

from buildkit.commands import ReleaseBuild
from buildkit.options import default_build_options
from buildkit.plan import BuildPlan
from setuptools import setup


BASE_DIR = Path(__file__).resolve().parent

# 解析 --old / --release
options = default_build_options()

# 可选：启用临时目录构建，避免删除本地源码
# options.use_temp_build = True

# 可选：预览 --release 的清理动作（不删除文件）
# 用法：python setup.py bdist_wheel --dry-run
# 注意：python setup.py develop 为源码链接安装，不执行 release 清理。

# 可选：排除某些包或源文件
# options.exclude_packages = ["tests", "examples*"]
# options.exclude_sources = ["**/migrations/*.py", "**/legacy/*.py"]
# options.exclude_modules = ["yourpkg/sms/pipeline.py"]
# options.exclude_source_dirs = ["node_modules", "dist"]
# options.use_gitignore = True  # 使用 .gitignore 过滤临时目录复制
# options.use_namespace_packages = True  # 命名空间包使用 find_namespace_packages

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
    
    # 写法一：src 布局 (Standard src-layout)
    # 最推荐的做法。项目根目录下有个 src/ 文件夹，里面才是包。
    # "" 表示根搜索路径，"src" 表示去该目录下找 packages 中列出的包。
    packages=["good_python", "good_python.core"],
    package_dir={"": "src"},

    # --- 或者 ---

    # 写法二：平铺布局 (Flat layout)
    # 如果你的 good_python 文件夹直接就在项目根目录下（没有 src 文件夹）。
    # 此时不需要 package_dir 映射，或者映射为空。
    # packages=["good_python", "good_python.core"],
    # package_dir={"": "."},

    asset_copy_hook=copy_assets,
)

setup_kwargs, ext_modules = plan.build()
setup_kwargs["cmdclass"] = plan.cmdclass(build_ext_cls=BuildExt)

setup(
    name="good_python",
    version="0.1.0",
    description="Short package description",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="you@example.com",
    url="https://example.com/good_python",
    license="MIT",
    python_requires=">=3.9",
    install_requires=[],
    extras_require={},
    ext_modules=ext_modules,
    include_package_data=True,
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
