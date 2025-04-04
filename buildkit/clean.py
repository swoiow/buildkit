import os
import shutil
from pathlib import Path

from setuptools import Command


TEMP_BUILD_DIR = os.environ.get("BUILD_TEMP_DIR", ".build_package_tmp")


class CleanCommand(Command):
    """
    清理 build 目录、临时目录、.so/.pyd/.c 文件。
    """

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suffixes = ["*.c", "*.so", "*.pyd"]
        for suf in suffixes:
            for f in Path(".").rglob(suf):
                try:
                    f.unlink()
                    print(f"🗑 Removed {f}")
                except Exception as e:
                    print(f"⚠ Failed to remove {f}: {e}")
        shutil.rmtree("build", ignore_errors=True)
        shutil.rmtree(TEMP_BUILD_DIR, ignore_errors=True)
