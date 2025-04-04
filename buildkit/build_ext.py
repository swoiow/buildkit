import os
import shutil
import sysconfig

from setuptools.command.build_ext import build_ext


class BuildExtCommand(build_ext):

    def find_package_modules(self, package, package_dir):
        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        modules = super().find_package_modules(package, package_dir)
        return [
            (pkg, mod, filepath)
            for pkg, mod, filepath in modules
            if not os.path.exists(filepath.replace(".py", ext_suffix))
        ]

    def build_extension(self, ext):
        super().build_extension(ext)

        ext_path = self.get_ext_fullpath(ext.name)
        dist_dir = os.path.join(os.path.dirname(__file__), "..", "dist")
        os.makedirs(dist_dir, exist_ok=True)

        dest_path = os.path.join(dist_dir, os.path.basename(ext_path))
        shutil.copy(ext_path, dest_path)

        print(f"📦 Copied built extension {ext.name} → {dest_path}")
