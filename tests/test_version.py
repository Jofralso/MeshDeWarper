"""Tests for version module."""

from cura_xy_calibration.__version__ import __version__, __version_info__


class TestVersion:
    def test_version_string(self) -> None:
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_info(self) -> None:
        assert isinstance(__version_info__, tuple)
        assert len(__version_info__) == 3
        assert all(isinstance(v, int) for v in __version_info__)

    def test_version_consistency(self) -> None:
        expected = ".".join(str(v) for v in __version_info__)
        assert __version__ == expected
