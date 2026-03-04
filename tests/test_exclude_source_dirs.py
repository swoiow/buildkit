from buildkit.cython import discover_sources_from_packages
from buildkit.runtime import set_dry_run


def test_exclude_source_dirs_blocks_nested_folder(monkeypatch, capsys) -> None:
    from pathlib import Path

    def fake_exists(self) -> bool:
        return self.as_posix() == "demo"

    def fake_rglob(self, pattern):
        assert pattern == "*.py"
        return [Path("demo/data/etl.py"), Path("demo/core.py")]

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(Path, "rglob", fake_rglob)
    set_dry_run(True)
    try:
        sources = discover_sources_from_packages(
            packages=["demo"],
            package_dir={"demo": "demo"},
            exclude_globs=[],
            exclude_dirs={"data"},
        )
    finally:
        set_dry_run(False)

    out = capsys.readouterr().out
    assert "[DRY-RUN] Would exclude source" in out
    assert all("data" not in src.as_posix() for src in sources)
    assert any(src.name == "core.py" for src in sources)
