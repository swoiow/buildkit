from pathlib import Path
from sysconfig import get_config_vars

from setuptools import find_packages


def get_cpy_suffix():
    return Path(get_config_vars()["EXT_SUFFIX"]).suffix


def collect_packages(**kwargs):
    """
    获取有效的 packages 列表（带扩展钩子）。

    示例:
    >>> collect_packages(exclude=["tests", "examples"])
    """
    return find_packages(**kwargs)
