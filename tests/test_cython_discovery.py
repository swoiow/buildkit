from buildkit.cython import discover_sources_from_packages
from buildkit.runtime import set_dry_run


def test_discover_sources_logs_excluded_in_dry_run(monkeypatch, capsys) -> None:
    from pathlib import Path

    def fake_exists(self) -> bool:
        return self.as_posix() == "demo"

    def fake_rglob(self, pattern):
        assert pattern == "*.py"
        return [Path("demo/pipeline.py"), Path("demo/core.py"), Path("demo/__init__.py")]

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(Path, "rglob", fake_rglob)
    set_dry_run(True)
    try:
        sources = discover_sources_from_packages(
            packages=["demo"],
            package_dir={"demo": "demo"},
            exclude_globs=["**/pipeline.py"],
            exclude_dirs=set(),
        )
    finally:
        set_dry_run(False)

    out = capsys.readouterr().out
    assert "[DRY-RUN] Would exclude source" in out
    assert all(src.name != "pipeline.py" for src in sources)
    assert any(src.name == "core.py" for src in sources)
