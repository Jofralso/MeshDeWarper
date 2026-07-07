"""Ultimaker Cura plugin entry point."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from cura_xy_calibration.__version__ import __version__
from cura_xy_calibration.core import Calibration, CalibrationProfile
from cura_xy_calibration.gcode.warper import GCodeWarper
from cura_xy_calibration.interpolation import BilinearInterpolation, InterpolationAlgorithm

logger = logging.getLogger(__name__)

PLUGIN_NAME = "XY Distortion Calibration"
PLUGIN_VERSION = __version__


class CuraPlugin:
    """Main plugin class for Ultimaker Cura integration.

    Manages plugin lifecycle, settings, and G-code post-processing.
    """

    def __init__(self) -> None:
        self._calibration: Calibration | None = None
        self._profile: CalibrationProfile | None = None
        self._enabled: bool = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        logger.info("Plugin %s", "enabled" if enabled else "disabled")

    def get_calibration(self) -> Calibration | None:
        return self._calibration

    def set_calibration(self, calibration: Calibration) -> None:
        self._calibration = calibration
        logger.info("Calibration updated (%d points)", self._calibration.mesh.num_points)

    def load_profile(self, path: Path) -> CalibrationProfile:
        """Load a calibration profile from file."""
        profile = CalibrationProfile.load(path)
        self._profile = profile

        # Reconstruct calibration from profile
        interp = self._interpolation_from_name(profile.interpolation)
        self._calibration = Calibration.from_profile(profile, interp)

        logger.info("Profile loaded: %s (%s)", path, profile.printer)
        return profile

    def save_profile(self, path: Path) -> None:
        """Save current calibration state to a profile file."""
        if self._calibration is None:
            msg = "No calibration to save"
            raise RuntimeError(msg)
        profile = self._calibration.to_profile()
        profile.save(path)
        self._profile = profile

    def warp_gcode(self, input_path: Path, output_path: Path) -> None:
        """Warp a G-code file using the current calibration."""
        if not self._enabled:
            logger.info("Plugin disabled, copying G-code without warping")
            input_path.write_text(output_path.read_text() if output_path.exists() else "")
            return

        if self._calibration is None:
            msg = "No calibration loaded; cannot warp G-code"
            raise RuntimeError(msg)

        warper = GCodeWarper(self._calibration)
        warper.warp_file(input_path, output_path)

    def reset_calibration(self) -> None:
        """Reset all offsets to zero."""
        if self._calibration is not None:
            self._calibration.mesh.reset_offsets()
            logger.info("Calibration reset")

    @staticmethod
    def _interpolation_from_name(name: str) -> InterpolationAlgorithm:
        """Resolve an interpolation algorithm by name."""
        algos: dict[str, Callable[[], InterpolationAlgorithm]] = {
            "bilinear": lambda: BilinearInterpolation(),
        }
        try:
            from cura_xy_calibration.interpolation.bicubic import BicubicInterpolation

            algos["bicubic"] = lambda: BicubicInterpolation()

            from cura_xy_calibration.interpolation.tps import ThinPlateSplineInterpolation

            algos["thin_plate_spline"] = lambda: ThinPlateSplineInterpolation()

            from cura_xy_calibration.interpolation.rbf import RBFInterpolation

            algos["rbf_multiquadric"] = lambda: RBFInterpolation(kernel="multiquadric")
        except ImportError:
            pass

        factory = algos.get(name)
        if factory is None:
            logger.warning("Unknown interpolation '%s', falling back to bilinear", name)
            factory = algos["bilinear"]

        return factory()


# Cura extension registration
def get_meta_data() -> dict[str, Any]:
    return {
        "version": PLUGIN_VERSION,
        "plugin_name": PLUGIN_NAME,
        "supported_cura_versions": [">=5.0"],
    }


def register() -> CuraPlugin:
    """Register the plugin with Cura's extension system."""
    plugin = CuraPlugin()
    logger.info("%s v%s registered", PLUGIN_NAME, PLUGIN_VERSION)
    return plugin
