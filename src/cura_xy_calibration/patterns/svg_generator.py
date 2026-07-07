"""SVG calibration pattern generator."""

from __future__ import annotations

import logging
from pathlib import Path

import svgwrite

from cura_xy_calibration.patterns.base import (
    FiducialMarker,
    PatternConfig,
    PatternGenerator,
    PointStyle,
)

logger = logging.getLogger(__name__)


class SvgPatternGenerator(PatternGenerator):
    """Generates dimensionally accurate calibration patterns as SVG.

    SVG output is resolution-independent and suitable for printing
    or direct import into design software.
    """

    def generate(self, config: PatternConfig, output_path: Path) -> Path:
        output_path = output_path.with_suffix(".svg")

        cols = int(config.bed_width / config.spacing) + 1
        rows = int(config.bed_height / config.spacing) + 1

        grid_w = (cols - 1) * config.spacing
        grid_h = (rows - 1) * config.spacing
        margin = config.margin

        dwg = svgwrite.Drawing(
            str(output_path),
            size=(f"{grid_w + 2 * margin}mm", f"{grid_h + 2 * margin}mm"),
            viewBox=f"0 0 {grid_w + 2 * margin} {grid_h + 2 * margin}",
        )

        # Add background
        dwg.add(dwg.rect((0, 0), (grid_w + 2 * margin, grid_h + 2 * margin), fill="white"))

        for row in range(rows):
            for col in range(cols):
                px = margin + col * config.spacing
                py = margin + row * config.spacing
                self._draw_point(dwg, px, py, config)

                if config.show_numbers:
                    num = row * cols + col + 1
                    dwg.add(
                        dwg.text(
                            str(num),
                            insert=(px + config.point_size + 0.5, py + 0.5),
                            font_size=f"{config.number_font_size}mm",
                            font_family="monospace",
                            fill="black",
                        )
                    )

        if config.fiducial != FiducialMarker.NONE:
            self._draw_fiducials(dwg, margin, margin, grid_w, grid_h, config)

        dwg.save()
        logger.info("SVG pattern generated: %s", output_path)
        return output_path

    def _draw_point(self, dwg: svgwrite.Drawing, x: float, y: float, config: PatternConfig) -> None:
        sz = config.point_size
        if config.point_style == PointStyle.CROSS:
            dwg.add(dwg.line((x - sz, y), (x + sz, y), stroke="black"))
            dwg.add(dwg.line((x, y - sz), (x, y + sz), stroke="black"))
        elif config.point_style == PointStyle.DOT:
            dwg.add(dwg.circle((x, y), sz / 2, fill="black"))
        elif config.point_style == PointStyle.CIRCLE:
            dwg.add(dwg.circle((x, y), sz, fill="none", stroke="black"))
        elif config.point_style == PointStyle.TARGET:
            dwg.add(dwg.circle((x, y), sz, fill="none", stroke="black"))
            dwg.add(dwg.circle((x, y), sz / 3, fill="black"))

    def _draw_fiducials(
        self,
        dwg: svgwrite.Drawing,
        ox: float,
        oy: float,
        w: float,
        h: float,
        config: PatternConfig,
    ) -> None:
        corners = [(ox, oy), (ox + w, oy), (ox, oy + h), (ox + w, oy + h)]
        sz = config.fiducial_size

        for cx, cy in corners:
            if config.fiducial == FiducialMarker.CORNER_CROSS:
                dwg.add(
                    dwg.line((cx - sz, cy - sz), (cx + sz, cy + sz), stroke="black", stroke_width=1)
                )  # noqa: E501
                dwg.add(
                    dwg.line((cx + sz, cy - sz), (cx - sz, cy + sz), stroke="black", stroke_width=1)
                )  # noqa: E501
            elif config.fiducial == FiducialMarker.CORNER_CIRCLE:
                dwg.add(dwg.circle((cx, cy), sz, fill="none", stroke="black"))
            elif config.fiducial == FiducialMarker.CORNER_TARGET:
                dwg.add(dwg.circle((cx, cy), sz, fill="none", stroke="black"))
                dwg.add(dwg.circle((cx, cy), sz * 0.6, fill="none", stroke="black"))
