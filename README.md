# buildkit

English docs: this file.  
Chinese docs: `README-CN.md`.

buildkit is a pragmatic `setup.py` build toolkit for projects that need dynamic build logic, Cython-first release flows, and source-stripping controls.

## Why Buildkit
- Reusable build orchestration across multiple repositories.
- Native release flow: compile -> package -> strip `.py/.c` outputs.
- Fine-grained controls for package/source/module exclusion.
- Works with classic setuptools workflows where `pyproject.toml` alone is too static.

## Quick Start
- Editable install: `python -m pip install -e .`
- Build wheel: `python -m build --wheel`
- Release wheel: `python setup.py bdist_wheel --release`
- Release preview: `python setup.py bdist_wheel --dry-run`
- Generate setup template: `python -m buildkit init`
- Alias command: `python -m buildkit setup`

## Build Flags
- `--old`: skip Cython/release behavior.
- `--release`: enable release stripping logic.
- `--dry-run`: preview stripping/filtering without deleting files.

Environment flags:
- `BUILDKIT_DRY_RUN=1`
- `BUILDKIT_RELEASE=1`
- `BUILDKIT_OLD=1`

CLI flags take precedence. `--old` overrides `--release` and `--dry-run`.

## Common Configuration
- `options.exclude_packages`: exclude package/subpackage names.
- `options.exclude_sources`: exclude Cython source scan.
- `options.exclude_modules`: exclude modules from `build_py` output (wheel content).
- `options.exclude_source_dirs`: directory-level Cython scan exclusion.
- `keep_files` in `ReleaseBuild`: keep file names from release stripping.

## Buildkit vs Modern Tools vs PEP Standards (2026)

| Feature | Buildkit (Pragmatic) | uv / Hatch / Poetry (Modern) | Official PEP Standards |
| --- | --- | --- | --- |
| Primary Logic | Dynamic `setup.py` | Declarative `pyproject.toml` | Standardized metadata/contracts |
| Versioning | Dynamic logic supported | Mostly static + plugins | Static-oriented metadata model |
| Source Protection | Native release stripping workflow | Usually not built-in | Not a focus of standards |
| Build Flow | Imperative, filesystem-level control | Standardized and predictable | Frontend/backend decoupling |

### Positioning
- `uv` is excellent for speed and env/dependency operations, but specialized packaging logic still depends on backend behavior.
- `Hatch` supports custom hooks, but equivalent behavior often requires plugin-level work.
- buildkit focuses on high-control packaging scenarios: Cython-heavy builds, source stripping, and conditional build logic.

### PEP Relationship
- PEP 517/518: compatible (via setuptools backend usage).
- PEP 621: intentionally less strict in practice when dynamic metadata/build logic is required.
- PEP 660: handled with explicit `develop` command behavior (warns that release stripping does not apply to editable-like flow).

## FAQ
- Why are `.py` files still visible in release wheels?
`build_py` can re-copy Python sources after `build_ext`; buildkit uses `ReleaseBuildPy` to strip again.
- Does `exclude_sources` remove files from wheel?
No. It only affects Cython source scanning. Use `exclude_modules` for wheel-level module exclusion.
- Does `setup.py develop` apply release stripping?
No. It links source in place; buildkit warns when release flags are used there.

## Reference Docs
- `docs/examples/README.md`
- `docs/reference-cases.md`
- `docs/test-cases.md`

## TODO
- Add path-level keep rules (for example `keep_module_globs`) to preserve selected `.py` files in release wheels without relying on filename-only `keep_files`.
