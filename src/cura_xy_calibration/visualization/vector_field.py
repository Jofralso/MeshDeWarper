"""Vector field renderer for distortion offset visualisation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from cura_xy_calibration.core.mesh import Mesh

logger = logging.getLogger(__name__)


@dataclass
class VectorFieldConfig:
    """Configuration for vector field rendering.

    Attributes:
        scale: Arrow scale factor.
        width: Arrow line width.
        color: Arrow colour.
        alpha: Arrow transparency.
        subsample: Subsample factor for dense grids.
        title: Plot title.
        dpi: Output resolution.
        figsize: Figure size in inches.
    """

    scale: float = 1.0
    width: float = 0.003
    color: str = "#c00000"
    alpha: float = 0.8
    subsample: int = 1
    title: str = "Distortion Vector Field"
    dpi: int = 150
    figsize: tuple[float, float] = (8.0, 8.0)


class VectorFieldRenderer:
    """Renders a vector field showing direction and magnitude of offsets."""

    def __init__(self, config: VectorFieldConfig | None = None) -> None:
        self._config = config or VectorFieldConfig()

    def render(self, mesh: Mesh, output_path: Path) -> Path:
        """Generate a vector field image of distortion offsets.

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

        cfg = self._config
        step = cfg.subsample

        # Collect vectors for visualisation
        x_pos = []
        y_pos = []
        u_vals = []
        v_vals = []
        magnitudes = []

        for row in range(0, mesh.rows, step):
            for col in range(0, mesh.cols, step):
                p = mesh[row, col]
                if abs(p.offset_x) < 1e-10 and abs(p.offset_y) < 1e-10:
                    continue
                x_pos.append(p.x)
                y_pos.append(p.y)
                u_vals.append(p.offset_x)
                v_vals.append(p.offset_y)
                magnitudes.append(p.magnitude)

        if not x_pos:
            logger.warning("No non-zero offsets to plot")
            fig, ax = plt.subplots(figsize=cfg.figsize)
            ax.text(0.5, 0.5, "No distortion offsets", ha="center", va="center")
            ax.set_xlabel("X (mm)")
            ax.set_ylabel("Y (mm)")
            ax.set_title(cfg.title)
            fig.tight_layout()
            fig.savefig(str(output_path), dpi=cfg.dpi)
            plt.close(fig)
            return output_path

        fig, ax = plt.subplots(figsize=cfg.figsize)

        q = ax.quiver(
            x_pos,
            y_pos,
            u_vals,
            v_vals,
            magnitudes,
            scale=cfg.scale,
            width=cfg.width,
            color=cfg.color,
            alpha=cfg.alpha,
            cmap="viridis",
        )

        ax.quiverkey(q, 0.9, 0.95, 1.0, "mm", coordinates="figure", labelpos="E")

        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_title(cfg.title)
        ax.set_aspect("equal")
        ax.set_xlim(0, mesh.width)
        ax.set_ylim(0, mesh.height)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        fig.savefig(str(output_path), dpi=cfg.dpi)
        plt.close(fig)

        logger.info("Vector field saved to %s", output_path)
        return output_path
