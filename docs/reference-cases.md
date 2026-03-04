# Buildkit Reference Cases

Use this document to quickly map a packaging problem to the best reference project or example.

## 1) Minimal Runnable `setup.py`
- Situation: Validate a basic `BuildPlan` flow first, without advanced excludes or temp build.
- Reference: `docs/examples/01-minimal.md`

## 2) Release Mode (Hide Source Files)
- Situation: You need `--release` to strip `.py/.c` while keeping required entry files.
- Reference: `docs/examples/02-release.md`
- Key point: Define keep files in `BuildExt.keep_files`, for example `{"__init__.py", "pkg_info.py", "version.py"}`.

## 3) Safe Local Build with Temporary Directory
- Situation: You want to avoid touching local source files while building wheels.
- Reference: `docs/examples/03-temp-build-assets.md`
- Key point: Enable `options.use_temp_build = True`; default temp directory is `.build_package_tmp`.

## 4) Temp Build + Static Asset Copy
- Situation: Build output must include static assets such as `icon/js/html/templates`.
- Reference: `docs/examples/03-temp-build-assets.md`
- Key point: Implement `asset_copy_hook` to copy static assets after source copy.

## 5) Exclude Subpackages (for example `data/providers`)
- Situation: Specific subpackages should not be compiled or packaged.
- Reference: `M:\\CodeHub\\pytrade-sms\\setup.py`
- Recommended config:
```python
exclude_packages = [
    "pytrade.data",
    "pytrade.data.*",
    "pytrade.providers",
    "pytrade.providers.*",
]
```

## 6) Namespace Packages (No `__init__.py`)
- Situation: Top-level package directory has no `__init__.py` (PEP 420).
- Reference: `M:\\CodeHub\\pytrade-sms\\setup.py`
- Key point:
```python
options.use_namespace_packages = True
```

## 7) Regular Packages (With `__init__.py`)
- Situation: Standard Python package layout.
- Reference: `M:\\CodeHub\\pytrade-tdx\\setup.py`, `docs/examples/02-release.md`
- Key point: Default `find_packages` behavior is enough; namespace mode is not required.

## 8) Auto-read Version
- Situation: Read package version from `version.py`.
- Reference: `buildkit/version.py` + `M:\\CodeHub\\pytrade-tdx\\setup.py`
- Key point: `read_version(path)` supports both string and tuple formats.

## 9) Cython Directive Strategy
- Situation: Switch between simple and high-performance Cython directives.
- Reference: `buildkit/cython.py`
- Key points:
- Simple: `CYTHON_DIRECTIVES_SIMPLE`
- Advanced: `CYTHON_DIRECTIVES_FULL`

## 10) Quick Template Initialization
- Situation: Bootstrap a new project with a ready-to-use setup template.
- Reference: `buildkit/template.py`, `buildkit/cli.py`
- Command:
```bash
python -m buildkit init
```

## 11) Exclude a Single Module File (Remove from Wheel)
- Situation: Keep the package but remove specific `.py` modules from wheel output.
- Reference: `buildkit/commands.py` (`ReleaseBuildPy`)
- Key point:
```python
options.exclude_modules = ["pipeline.py", "aaa/etl.py"]
```

## 12) Preview Release Cleanup (`dry-run`)
- Situation: You want to inspect what `--release` would remove, without deleting files.
- Reference: `buildkit/release.py`, `buildkit/commands.py`
- Command:
```bash
python setup.py bdist_wheel --dry-run
```
