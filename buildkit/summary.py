import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from distutils.dir_util import copy_tree

from .options import BuildOptions


def print_summary(
    package_list: List[str],
    ext_list: Optional[List] = None,
    exclude_files: Optional[List[str]] = None,
    options: Optional[BuildOptions] = None,
) -> None:
    """打印构建摘要信息。

    :param package_list: package list.
    :param ext_list: extension list.
    :param exclude_files: excluded files list.
    :param options: build options.
    :return: None.
    """
    flags = options.flags if options else None
    print("[SUMMARY] Build Summary")
    print(" ├─ OS:", platform.system(), "/", platform.platform())
    print(" ├─ Python:", platform.python_version())
    print(f" ├─ Packages: {len(package_list)}")
    print(f" ├─ Extensions: {len(ext_list or [])}")
    print(f" ├─ Files excluded: {len(exclude_files or [])}")
    if options:
        print(" ├─ Temp Build Dir:", "ENABLED" if options.use_temp_build else "DISABLED")
        print(" ├─ Release Mode:", "ON" if flags and flags.is_release else "OFF")
        print(" ├─ Old Mode:", "ON" if flags and flags.is_old else "OFF")
    print(f" └─ DEBUG: {os.environ.get('DEBUG', '0')}")


def copy_to_temp_build_dir(
    package_list: List[str],
    base: str = ".",
    target: Optional[str] = None,
    options: Optional[BuildOptions] = None,
) -> str:
    """将要打包的 packages 拷贝到临时目录中。

    :param package_list: package list.
    :param base: base dir.
    :param target: target temp dir.
    :param options: build options.
    :return: temp dir path.
    """
    if options and target is None:
        target = options.temp_build_dir
    tmp_dir = Path(target or ".build_package_tmp")
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

    print(f"[COPY] Copied source files to temporary dir: {tmp_dir}")
    return str(tmp_dir)


def get_package_dir_mapping(packages: List[str], tmp_dir: str) -> Dict[str, str]:
    """为 setup(package_dir=...) 自动生成映射关系。

    :param packages: package list.
    :param tmp_dir: temp dir.
    :return: package dir mapping.
    """
    mapping: Dict[str, str] = {}
    for pkg in packages:
        top_pkg = pkg.split(".")[0]
        if top_pkg not in mapping:
            mapping[top_pkg] = str(Path(tmp_dir) / top_pkg)
    return mapping
