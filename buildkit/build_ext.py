import shutil
from pathlib import Path

from setuptools.command.build_ext import build_ext

from buildkit.utils import get_cpy_suffix


class BuildExtCommand(build_ext):

    def find_package_modules(self, package, package_dir):
        ext_suffix = get_cpy_suffix()
        modules = super().find_package_modules(package, package_dir)
        return [
            (pkg, mod, filepath)
            for pkg, mod, filepath in modules
            if not Path(filepath.replace(".py", ext_suffix)).exists()
        ]

    def build_extension(self, ext):
        super().build_extension(ext)

        ext_path = Path(self.get_ext_fullpath(ext.name))
        dist_dir = Path(__file__).resolve().parent.parent / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dist_dir / ext_path.name
        shutil.copy2(ext_path, dest_path)

        print(f"📦 Copied built extension {ext.name} → {dest_path}")
