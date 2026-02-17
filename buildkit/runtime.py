import os


DRY_RUN_ENV = "BUILDKIT_DRY_RUN"
RELEASE_ENV = "BUILDKIT_RELEASE"
OLD_ENV = "BUILDKIT_OLD"


def _env_truthy(name: str) -> bool:
    value = os.environ.get(name, "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _set_env_flag(name: str, enabled: bool) -> None:
    os.environ[name] = "1" if enabled else "0"


def set_dry_run(enabled: bool) -> None:
    """设置 dry-run 环境变量。

    :param enabled: whether to enable dry-run.
    :return: None.
    """
    _set_env_flag(DRY_RUN_ENV, enabled)


def set_release(enabled: bool) -> None:
    """设置 release 环境变量。

    :param enabled: whether to enable release.
    :return: None.
    """
    _set_env_flag(RELEASE_ENV, enabled)


def set_old(enabled: bool) -> None:
    """设置 old 环境变量。

    :param enabled: whether to enable old.
    :return: None.
    """
    _set_env_flag(OLD_ENV, enabled)


def is_dry_run() -> bool:
    """判断是否处于 dry-run 模式。

    :return: True when dry-run enabled.
    """
    return _env_truthy(DRY_RUN_ENV)


def is_release_env() -> bool:
    """判断是否设置 release 环境变量。

    :return: True when release env enabled.
    """
    return _env_truthy(RELEASE_ENV)


def is_old_env() -> bool:
    """判断是否设置 old 环境变量。

    :return: True when old env enabled.
    """
    return _env_truthy(OLD_ENV)
