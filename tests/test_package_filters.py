from buildkit.package import split_packages


def test_exclude_package_boundary_match() -> None:
    included, excluded = split_packages(
        ["pytrade.data", "pytrade.data.jobs", "pytrade.database"],
        ["pytrade.data"],
    )
    assert "pytrade.data" in excluded
    assert "pytrade.data.jobs" in excluded
    assert "pytrade.database" in included
