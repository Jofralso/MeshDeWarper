"""Heatmap renderer for distortion magnitude visualisation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from cura_xy_calibration.core.mesh import Mesh

logger = logging.getLogger(__name__)

COLORMAPS = frozenset(
    {
        "viridis",
        "plasma",
        "inferno",
        "magma",
        "jet",
        "coolwarm",
        "RdYlBu_r",
        "RdYlGn_r",
    }
)


@dataclass
class HeatmapConfig:
    """Configuration for heatmap rendering.

    Attributes:
        colormap: Matplotlib colormap name.
        dpi: Output resolution.
        figsize: Figure size in inches.
        show_colorbar: Whether to include colour bar.
        show_grid: Whether to overlay the calibration grid.
        title: Plot title.
        vmin: Min colour value (auto if None).
        vmax: Max colour value (auto if None).
    """

    colormap: str = "viridis"
    dpi: int = 150
    figsize: tuple[float, float] = (8.0, 8.0)
    show_colorbar: bool = True
    show_grid: bool = True
    title: str = "Distortion Magnitude (mm)"
    vmin: float | None = None
    vmax: float | None = None


class HeatmapRenderer:
    """Renders a colour-mapped heatmap of distortion magnitudes over the bed."""

    def __init__(self, config: HeatmapConfig | None = None) -> None:
        self._config = config or HeatmapConfig()

    def render(self, mesh: Mesh, output_path: Path, resolution: int = 200) -> Path:
        """Generate a heatmap image of distortion magnitudes.

        Args:
            mesh: The distortion mesh to visualise.
            output_path: Output image path (.png).
            resolution: Interpolation resolution for the heatmap.

        Returns:
            Path to the generated image.
        """
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        output_path = output_path.with_suffix(".png")

        # Build a regular grid for the heatmap
        xs = np.linspace(0, mesh.width, resolution)
        ys = np.linspace(0, mesh.height, resolution)
        X, Y = np.meshgrid(xs, ys)

        # Compute offset magnitude at each grid point via bilinear fallback
        Z = np.zeros_like(X)
        from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation

        interp = BilinearInterpolation()

        for i in range(resolution):
            for j in range(resolution):
                ox, oy = interp.interpolate(mesh, float(X[i, j]), float(Y[i, j]))
                Z[i, j] = np.hypot(ox, oy)

        fig, ax = plt.subplots(figsize=self._config.figsize)
        cmap = self._config.colormap
        if cmap not in COLORMAPS:
            logger.warning("Unknown colormap '%s', falling back to viridis", cmap)
            cmap = "viridis"

        im = ax.pcolormesh(
            X,
            Y,
            Z,
            cmap=cmap,
            shading="auto",
            vmin=self._config.vmin,
            vmax=self._config.vmax,
        )

        if self._config.show_colorbar:
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label("Offset magnitude (mm)")

        if self._config.show_grid:
            for row in range(mesh.rows):
                px = [mesh[row, c].x for c in range(mesh.cols)]
                py = [mesh[row, c].y for c in range(mesh.cols)]
                ax.plot(px, py, "k-", linewidth=0.3, alpha=0.5)
            for col in range(mesh.cols):
                px = [mesh[r, col].x for r in range(mesh.rows)]
                py = [mesh[r, col].y for r in range(mesh.rows)]
                ax.plot(px, py, "k-", linewidth=0.3, alpha=0.5)

        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_title(self._config.title)
        ax.set_aspect("equal")
        ax.set_xlim(0, mesh.width)
        ax.set_ylim(0, mesh.height)

        fig.tight_layout()
        fig.savefig(str(output_path), dpi=self._config.dpi)
        plt.close(fig)

        logger.info("Heatmap saved to %s", output_path)
        return output_path
