"""PDF calibration pattern generator using reportlab."""

from __future__ import annotations

import logging
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

from mesh_de_warper.patterns.base import (
    FiducialMarker,
    PatternConfig,
    PatternGenerator,
    PointStyle,
)

logger = logging.getLogger(__name__)

PAPER_SIZES = {
    "A4": A4,
    "A3": (420 * mm, 297 * mm),
    "letter": (612, 792),
    "tabloid": (792, 1224),
}


class PdfPatternGenerator(PatternGenerator):
    """Generates dimensionally accurate calibration patterns as PDF.

    Uses reportlab for precise vector output suitable for printing.
    Supports configurable paper sizes, margins, and fiducial markers.
    """

    def __init__(self, paper_size: str = "A4", landscape_mode: bool = True) -> None:
        self._paper_size = paper_size
        self._landscape = landscape_mode

    def generate(self, config: PatternConfig, output_path: Path) -> Path:
        """Generate a PDF calibration pattern."""
        output_path = output_path.with_suffix(".pdf")
        page_size = PAPER_SIZES.get(self._paper_size, A4)
        if self._landscape:
            page_size = landscape(page_size)

        c = pdf_canvas.Canvas(str(output_path), pagesize=page_size)
        width, height = page_size

        # Scale factor: mm -> points (1 mm = 72/25.4 points ≈ 2.835 pt)
        mm_to_pt = 72.0 / 25.4

        # Calculate grid dimensions
        cols = int(config.bed_width / config.spacing) + 1
        rows = int(config.bed_height / config.spacing) + 1

        # Centre the grid on the page
        grid_w = (cols - 1) * config.spacing * mm_to_pt
        grid_h = (rows - 1) * config.spacing * mm_to_pt
        offset_x = (width - grid_w) / 2
        offset_y = (height - grid_h) / 2

        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(0, 0, 0)

        for row in range(rows):
            for col in range(cols):
                px = offset_x + col * config.spacing * mm_to_pt
                py = offset_y + row * config.spacing * mm_to_pt

                self._draw_point(c, px, py, config)

                if config.show_numbers:
                    num = row * cols + col + 1
                    c.setFont("Helvetica", config.number_font_size * mm_to_pt)
                    c.drawString(
                        px + config.point_size * mm_to_pt + 1,
                        py - config.number_font_size * mm_to_pt / 3,
                        str(num),
                    )

        # Draw fiducial markers at corners
        if config.fiducial != FiducialMarker.NONE:
            self._draw_fiducials(c, offset_x, offset_y, grid_w, grid_h, config)

        c.save()
        logger.info("PDF pattern generated: %s", output_path)
        return output_path

    def _draw_point(self, c: pdf_canvas.Canvas, x: float, y: float, config: PatternConfig) -> None:
        sz = config.point_size * 72.0 / 25.4
        c.setLineWidth(0.5)

        if config.point_style == PointStyle.CROSS:
            c.line(x - sz, y, x + sz, y)
            c.line(x, y - sz, x, y + sz)
        elif config.point_style == PointStyle.DOT:
            c.circle(x, y, sz / 2, fill=1)
        elif config.point_style == PointStyle.CIRCLE:
            c.circle(x, y, sz, fill=0)
        elif config.point_style == PointStyle.TARGET:
            c.circle(x, y, sz, fill=0)
            c.circle(x, y, sz / 3, fill=1)

    def _draw_fiducials(
        self,
        c: pdf_canvas.Canvas,
        ox: float,
        oy: float,
        w: float,
        h: float,
        config: PatternConfig,
    ) -> None:
        corners = [(ox, oy), (ox + w, oy), (ox, oy + h), (ox + w, oy + h)]
        sz = config.fiducial_size * 72.0 / 25.4
        c.setLineWidth(1.0)

        for cx, cy in corners:
            if config.fiducial == FiducialMarker.CORNER_CROSS:
                c.line(cx - sz, cy - sz, cx + sz, cy + sz)
                c.line(cx + sz, cy - sz, cx - sz, cy + sz)
            elif config.fiducial == FiducialMarker.CORNER_CIRCLE:
                c.circle(cx, cy, sz, fill=0)
            elif config.fiducial == FiducialMarker.CORNER_TARGET:
                c.circle(cx, cy, sz, fill=0)
                c.circle(cx, cy, sz * 0.6, fill=0)
