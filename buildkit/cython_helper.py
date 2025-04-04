import json
import os
from pathlib import Path
from typing import Dict, List

from Cython.Build import cythonize
from Cython.Compiler.Errors import CompileError
from setuptools import Extension


CY_CACHE_FILE = ".cycache"


def find_cython_extensions_for_packages(
    packages: List[str],
    package_dir: Dict[str, str],
    exclude_init: bool = True
) -> List[Extension]:
    """
    查找逻辑包中的 .py 文件，并生成 Cython Extension 对象列表。

    示例:
    >>> find_cython_extensions_for_packages(["etl.commons"], {"etl": "."})
    """
    extensions = []
    for pkg in packages:
        parts = pkg.split(".")
        top_pkg = parts[0]
        base = package_dir.get(top_pkg, top_pkg)
        subdirs = parts[1:]
        pkg_dir = Path(base, *subdirs)
        if not pkg_dir.exists():
            continue
        for py_file in pkg_dir.rglob("*.py"):
            if exclude_init and py_file.name == "__init__.py":
                continue
            rel_path = py_file.relative_to(pkg_dir).with_suffix("")
            mod_name = pkg + "." + ".".join(rel_path.parts)
            extensions.append(Extension(mod_name, [str(py_file)]))
    return extensions


def safe_cythonize(extensions: List[Extension], compiler_directives: dict) -> List[Extension]:
    """
    安全执行 Cythonize，失败模块将跳过。

    示例:
    >>> safe_cythonize(exts, {"language_level": "3"})
    """
    good_extensions = []
    for ext in extensions:
        try:
            compiled = cythonize([ext], compiler_directives=compiler_directives)
            good_extensions.extend(compiled)
        except CompileError as e:
            print(f"❌ Error compiling {ext.name}: {e}. Skipping.")
        except Exception as e:
            print(f"❌ Unexpected error in {ext.name}: {e}. Skipping.")
    return good_extensions


def load_cy_cache() -> dict:
    """从缓存文件加载源文件的上次修改时间"""
    if Path(CY_CACHE_FILE).exists():
        return json.loads(Path(CY_CACHE_FILE).read_text())
    return {}


def save_cy_cache(file_mtime_map: dict):
    """保存源文件的当前修改时间到缓存文件"""
    Path(CY_CACHE_FILE).write_text(json.dumps(file_mtime_map, indent=2))


def collect_changed_sources(files: List[str]) -> List[str]:
    """
    根据 .cycache 检测哪些源文件发生变化。

    示例:
    >>> collect_changed_sources(["etl/commons/core.py", "etl/base.py"])
    """
    old = load_cy_cache()
    new = {}
    changed = []

    for f in files:
        if not Path(f).exists():
            continue
        mtime = os.path.getmtime(f)
        new[f] = mtime
        if old.get(f) != mtime:
            changed.append(f)

    save_cy_cache(new)
    return changed


def safe_incremental_cythonize(
    extensions: List[Extension],
    compiler_directives: dict,
    force: bool = False
) -> List[Extension]:
    """
    增量方式进行 cythonize，仅构建变更的模块。

    示例:
    >>> safe_incremental_cythonize(exts, {"language_level": "3"})
    """
    all_sources = [ext.sources[0] for ext in extensions]
    changed_files = collect_changed_sources(all_sources) if not force else all_sources

    filtered = [ext for ext in extensions if ext.sources[0] in changed_files]
    if not filtered:
        print("✅ No source changes detected. Skipping Cython build.")
        return []

    print(f"⚙️ Detected {len(filtered)} changed source file(s), rebuilding...")
    return safe_cythonize(filtered, compiler_directives)
