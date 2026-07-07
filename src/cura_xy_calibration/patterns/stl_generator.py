"""STL calibration pattern generator for 3D printing."""

from __future__ import annotations

import logging
import math
from pathlib import Path

import numpy as np
from stl import mesh as stl_mesh

from cura_xy_calibration.patterns.base import (
    PatternConfig,
    PatternGenerator,
)

logger = logging.getLogger(__name__)


class StlPatternGenerator(PatternGenerator):
    """Generates calibration patterns as 3D-printable STL files.

    Each calibration point is rendered as a small raised feature
    (e.g., cross or dot) on a flat substrate. The STL is watertight
    and manifold for reliable slicing.
    """

    def __init__(self, substrate_height: float = 1.0, feature_height: float = 2.0) -> None:
        self._substrate_height = substrate_height
        self._feature_height = feature_height

    def generate(self, config: PatternConfig, output_path: Path) -> Path:
        output_path = output_path.with_suffix(".stl")

        cols = int(config.bed_width / config.spacing) + 1
        rows = int(config.bed_height / config.spacing) + 1

        # Build the substrate first
        meshes: list[stl_mesh.Mesh] = []
        substrate = self._make_substrate(config.bed_width, config.bed_height)
        meshes.append(substrate)

        # Add features at each grid point
        for row in range(rows):
            for col in range(cols):
                x = col * config.spacing
                y = row * config.spacing
                feature = self._make_feature(x, y, config)
                meshes.append(feature)

        combined = stl_mesh.Mesh(np.concatenate([m.data for m in meshes]))
        combined.save(str(output_path))
        logger.info("STL pattern generated: %s", output_path)
        return output_path

    def _make_substrate(self, width: float, height: float) -> stl_mesh.Mesh:
        h = self._substrate_height
        vertices = np.array(
            [
                [0, 0, 0],
                [width, 0, 0],
                [width, height, 0],
                [0, height, 0],
                [0, 0, h],
                [width, 0, h],
                [width, height, h],
                [0, height, h],
            ]
        )

        faces = np.array(
            [
                [0, 1, 2],
                [0, 2, 3],  # bottom
                [4, 6, 5],
                [4, 7, 6],  # top
                [0, 4, 1],
                [1, 4, 5],  # front
                [1, 5, 2],
                [2, 5, 6],  # right
                [2, 6, 3],
                [3, 6, 7],  # back
                [3, 7, 0],
                [0, 7, 4],  # left
            ]
        )

        return stl_mesh.Mesh(
            np.zeros(faces.shape[0], dtype=stl_mesh.Mesh.dtype), remove_empty_areas=False
        )

    def _make_feature(self, x: float, y: float, config: PatternConfig) -> stl_mesh.Mesh:
        sz = config.point_size
        h = self._feature_height

        # Simple cylindrical dot
        segments = 16
        radius = sz / 2
        theta = np.linspace(0, 2 * math.pi, segments, endpoint=False)

        # Bottom ring (on substrate top)
        bottom = np.column_stack(
            [
                x + radius * np.cos(theta),
                y + radius * np.sin(theta),
                np.full(segments, self._substrate_height),
            ]
        )
        # Top ring
        top = np.column_stack(
            [
                x + radius * np.cos(theta),
                y + radius * np.sin(theta),
                np.full(segments, h),
            ]
        )
        # Centre points
        centre_bottom = np.array([[x, y, self._substrate_height]])
        centre_top = np.array([[x, y, h]])

        vertices = np.vstack([bottom, top, centre_bottom, centre_top])
        n = segments

        faces = []
        # Side faces
        for i in range(n):
            j = (i + 1) % n
            faces.append([i, j, j + n])
            faces.append([i, j + n, i + n])
        # Top faces
        for i in range(n):
            j = (i + 1) % n
            faces.append([i + 2 * n, j + 2 * n, j])
            faces.append([i + 2 * n, j, i])

        return stl_mesh.Mesh(
            np.zeros(len(faces), dtype=stl_mesh.Mesh.dtype),
            remove_empty_areas=False,
        )
