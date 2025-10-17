import os
import shutil
from pathlib import Path
from typing import List

from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.build_py import build_py as _build_py


BASE_DIR = Path(__file__).resolve().parent


class FilterBuildPy(_build_py):
    """
    支持 exclude_files 的 build_py 扩展。
    """

    def __init__(self, *args, exclude_files: List[str] = None, **kwargs):
        self.exclude_files = exclude_files or []
        super().__init__(*args, **kwargs)

    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        return [
            (pkg, mod, file)
            for pkg, mod, file in modules
            if not any(Path(file).match(pat) for pat in self.exclude_files)
        ]


class SmartBuildExt(_build_ext):
    """
    编译扩展后将 .so/.pyd 文件移动至项目根目录。
    """

    def build_extension(self, ext):
        super().build_extension(ext)
        ext_path = self.get_ext_fullpath(ext.name)
        dest = BASE_DIR.joinpath(os.path.basename(ext_path))
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(ext_path, dest)
        print(f"✔ Moved {ext_path} -> {dest}")
