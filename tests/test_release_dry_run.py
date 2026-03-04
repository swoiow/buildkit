from buildkit.release import strip_sources
from buildkit.runtime import set_dry_run


def test_strip_sources_dry_run_keeps_files(capsys) -> None:
    class FakePath:
        def __init__(self, value: str):
            self._value = value
            self.parts = tuple(value.split("/"))
            self.name = value.split("/")[-1]

        def __str__(self):
            return self._value

    class FakeBaseDir:
        def rglob(self, pattern):
            assert pattern == "*.py"
            return [FakePath("demo.py")]

    set_dry_run(True)
    try:
        removed = strip_sources(
            base_dir=FakeBaseDir(),
            patterns=["*.py"],
            keep_files=set(),
            skip_dirs=set(),
        )
    finally:
        set_dry_run(False)
    out = capsys.readouterr().out
    assert removed == 1
    assert "[DRY-RUN] Would remove" in out
