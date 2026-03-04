from buildkit.flags import BuildFlags
from buildkit.runtime import set_dry_run, set_old, set_release


def test_env_flags_without_cli() -> None:
    set_old(False)
    set_release(True)
    set_dry_run(False)
    try:
        flags = BuildFlags.from_argv(["setup.py"])
    finally:
        set_old(False)
        set_release(False)
        set_dry_run(False)
    assert flags.is_old is False
    assert flags.is_release is True
    assert flags.is_dry_run is False


def test_cli_old_overrides_release_env() -> None:
    set_old(False)
    set_release(True)
    set_dry_run(True)
    try:
        flags = BuildFlags.from_argv(["setup.py", "--old"])
    finally:
        set_old(False)
        set_release(False)
        set_dry_run(False)
    assert flags.is_old is True
    assert flags.is_release is False
    assert flags.is_dry_run is False
