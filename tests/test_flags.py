from buildkit.flags import BuildFlags


def test_old_overrides_release_and_dry_run_from_cli() -> None:
    flags = BuildFlags.from_argv(["setup.py", "--release", "--dry-run", "--old"])
    assert flags.is_old is True
    assert flags.is_release is False
    assert flags.is_dry_run is False


def test_dry_run_implies_release() -> None:
    flags = BuildFlags.from_argv(["setup.py", "--dry-run"])
    assert flags.is_dry_run is True
    assert flags.is_release is True
