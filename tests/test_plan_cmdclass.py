from pathlib import Path

from buildkit.flags import BuildFlags
from buildkit.options import BuildOptions
from buildkit.plan import BuildPlan


def test_cmdclass_injects_options_exclude_modules() -> None:
    options = BuildOptions(flags=BuildFlags(), base_dir=Path.cwd())
    options.exclude_modules = ["pipeline.py"]
    plan = BuildPlan(
        options=options,
        packages=["demo"],
        package_dir={"demo": "demo"},
    )
    cmdclass = plan.cmdclass()
    build_py_cls = cmdclass["build_py"]
    assert hasattr(build_py_cls, "exclude_module_globs")
    assert "pipeline.py" in build_py_cls.exclude_module_globs
    assert "develop" in cmdclass
