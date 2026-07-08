"""Calibration preview — combined heatmap + vector field overlay."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from mesh_de_warper.core.mesh import Mesh
from mesh_de_warper.visualization.heatmap import HeatmapConfig
from mesh_de_warper.visualization.vector_field import VectorFieldConfig

logger = logging.getLogger(__name__)


@dataclass
class PreviewConfig:
    """Configuration for combined calibration preview.

    Attributes:
        heatmap: Heatmap renderer configuration.
        vector_field: Vector field renderer configuration.
        overlay_alpha: Transparency of the vector overlay on the heatmap.
    """

    heatmap: HeatmapConfig = field(default_factory=HeatmapConfig)
    vector_field: VectorFieldConfig = field(default_factory=VectorFieldConfig)
    overlay_alpha: float = 0.7


class CalibrationPreview:
    """Generates a combined preview image with heatmap + vector overlay."""

    def __init__(self, config: PreviewConfig | None = None) -> None:
        self._config = config or PreviewConfig()

    def render(self, mesh: Mesh, output_path: Path) -> Path:
        """Generate a combined heatmap + vector field preview.

        Args:
            mesh: The distortion mesh to visualise.
            output_path: Output image path (.png).

        Returns:
            Path to the generated image.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        output_path = output_path.with_suffix(".png")
        resolution = 200

        # Build heatmap base
        xs = np.linspace(0, mesh.width, resolution)
        ys = np.linspace(0, mesh.height, resolution)
        X, Y = np.meshgrid(xs, ys)  # noqa: N806

        Z = np.zeros_like(X)  # noqa: N806
        from mesh_de_warper.interpolation.bilinear import BilinearInterpolation

        interp = BilinearInterpolation()

        for i in range(resolution):
            for j in range(resolution):
                ox, oy = interp.interpolate(mesh, float(X[i, j]), float(Y[i, j]))
                Z[i, j] = np.hypot(ox, oy)

        fig, ax = plt.subplots(figsize=self._config.heatmap.figsize)

        # Heatmap layer
        cmap = self._config.heatmap.colormap
        im = ax.pcolormesh(
            X,
            Y,
            Z,
            cmap=cmap,
            shading="auto",
            vmin=self._config.heatmap.vmin,
            vmax=self._config.heatmap.vmax,
        )

        if self._config.heatmap.show_colorbar:
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label("Offset magnitude (mm)")

        # Vector overlay
        vf = self._config.vector_field
        x_pos, y_pos, u_vals, v_vals = [], [], [], []
        step = vf.subsample or 1
        for row in range(0, mesh.rows, step):
            for col in range(0, mesh.cols, step):
                p = mesh[row, col]
                x_pos.append(p.x)
                y_pos.append(p.y)
                u_vals.append(p.offset_x)
                v_vals.append(p.offset_y)

        if x_pos:
            ax.quiver(
                x_pos,
                y_pos,
                u_vals,
                v_vals,
                alpha=self._config.overlay_alpha,
                scale=vf.scale,
                width=vf.width,
                color=vf.color,
            )

        # Grid overlay
        if self._config.heatmap.show_grid:
            for row in range(mesh.rows):
                px = [mesh[row, c].x for c in range(mesh.cols)]
                py = [mesh[row, c].y for c in range(mesh.cols)]
                ax.plot(px, py, "k-", linewidth=0.3, alpha=0.4)
            for col in range(mesh.cols):
                px = [mesh[r, col].x for r in range(mesh.rows)]
                py = [mesh[r, col].y for r in range(mesh.rows)]
                ax.plot(px, py, "k-", linewidth=0.3, alpha=0.4)

        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_title(self._config.heatmap.title)
        ax.set_aspect("equal")
        ax.set_xlim(0, mesh.width)
        ax.set_ylim(0, mesh.height)

        fig.tight_layout()
        fig.savefig(str(output_path), dpi=self._config.heatmap.dpi)
        plt.close(fig)

        logger.info("Calibration preview saved to %s", output_path)
        return output_path
