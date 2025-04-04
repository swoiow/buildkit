import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List

from distutils.dir_util import copy_tree


TEMP_BUILD_DIR = os.environ.get("BUILD_TEMP_DIR", ".build_package_tmp")
USE_TEMP_BUILD = os.environ.get("USE_TEMP_BUILD", "0") == "1"


def print_summary(
    package_list: List[str],
    ext_list: List = None,
    exclude_files: List[str] = None
):
    """打印构建摘要信息，展示平台、包数、扩展模块数、是否启用临时构建目录等。"""
    print("📦 Build Summary")
    print(" ├─ OS:", platform.system(), "/", platform.platform())
    print(" ├─ Python:", platform.python_version())
    print(f" ├─ Packages: {len(package_list)}")
    print(f" ├─ Extensions: {len(ext_list or [])}")
    print(f" ├─ Files excluded: {len(exclude_files or [])}")
    print(" ├─ Temp Build Dir:", "ENABLED" if USE_TEMP_BUILD else "DISABLED")
    print(f" └─ DEBUG: {os.environ.get('DEBUG', '0')}")


def copy_to_temp_build_dir(package_list: List[str], base: str = ".", target: str = TEMP_BUILD_DIR) -> str:
    """
    将要打包的 packages 拷贝到临时目录中，便于干净构建。
    """
    tmp_dir = Path(target)
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    for pkg in package_list:
        rel_path = pkg.replace(".", "/")
        src_path = Path(base) / rel_path
        dst_path = tmp_dir / rel_path
        if src_path.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            copy_tree(str(src_path), str(dst_path))

    print(f"📂 Copied source files to temporary dir: {tmp_dir}")
    return str(tmp_dir)


def get_package_dir_mapping(packages: List[str], tmp_dir: str = TEMP_BUILD_DIR) -> Dict[str, str]:
    """
    为 setup(package_dir=...) 自动生成映射关系。
    """
    mapping = {}
    for pkg in packages:
        top_pkg = pkg.split(".")[0]
        if top_pkg not in mapping:
            mapping[top_pkg] = str(Path(tmp_dir) / top_pkg)
    return mapping
