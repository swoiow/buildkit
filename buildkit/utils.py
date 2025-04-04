from setuptools import find_packages


def collect_packages(**kwargs):
    """
    获取有效的 packages 列表（带扩展钩子）。

    示例:
    >>> collect_packages(exclude=["tests", "examples"])
    """
    return find_packages(**kwargs)
