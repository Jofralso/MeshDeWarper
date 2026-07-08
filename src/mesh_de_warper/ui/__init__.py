"""UI components for the calibration editor."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from mesh_de_warper.ui.editor import CalibrationEditor
    from mesh_de_warper.ui.profile_manager import ProfileManager

    __all__ = [
        "CalibrationEditor",
        "ProfileManager",
    ]
except ImportError as e:
    logger.warning("UI module unavailable (%s). Install PyQt5 for the calibration editor.", e)

    class CalibrationEditor:  # type: ignore[no-redef]
        """Placeholder — PyQt5 required."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            msg = "CalibrationEditor requires PyQt5 (pip install MeshDeWarper[qt])"
            raise RuntimeError(msg)

    class ProfileManager:  # type: ignore[no-redef]
        """Placeholder — PyQt5 required."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            msg = "ProfileManager requires PyQt5 (pip install MeshDeWarper[qt])"
            raise RuntimeError(msg)

    __all__ = [
        "CalibrationEditor",
        "ProfileManager",
    ]
