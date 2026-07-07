# CuraXYCalibration

> Full XY distortion calibration plugin for Ultimaker Cura.

Characterize and compensate for non-linear positioning errors across the entire
printable area of your 3D printer. Warp G-code before export to correct XY
distortion with sub-millimeter precision.

## Features

- **Interactive Calibration Editor** — drag, snap, group edit, numeric entry
- **Calibration Pattern Generator** — print reference grids as PDF / SVG / STL
- **G-Code Warping Engine** — full AST parser, format-preserving output
- **Multiple Interpolation Algorithms** — bilinear, bicubic, thin plate splines, RBF
- **Heatmap & Vector Field Visualization** — see distortion at a glance
- **Calibration Profile Manager** — save, load, compare, import/export profiles
- **Experimental Computer Vision Assistant** — detect printed points from photos
- **100×100 Grid Support** — 10,000+ nodes with no UI freeze
- **Undo/Redo** — full operation history

## Installation

1. Download the latest `.curaplugin` from [Releases][releases].
2. In Cura, go to **Extensions → Manage Plugins**.
3. Click **Install from file** and select the downloaded package.
4. Restart Cura.

## Quick Start

```python
from cura_xy_calibration.core import Calibration, Point
from cura_xy_calibration.interpolation import BilinearInterpolation

# Create a calibration grid
cal = Calibration.for_bed(
    width=220, height=220, spacing=10,
    interpolation=BilinearInterpolation(),
)

# Warp G-code
warped = cal.warp_gcode("input.gcode", "output.gcode")
```

## Documentation

Full documentation is available at [cura-xy-calibration.readthedocs.io][docs].

## Development

```bash
git clone https://github.com/cura-xy-calibration/CuraXYCalibration.git
cd CuraXYCalibration
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,test]"
pre-commit install
pytest
```

## License

AGPL-3.0-only — see [LICENSE](LICENSE).

[releases]: https://github.com/cura-xy-calibration/CuraXYCalibration/releases
[docs]: https://cura-xy-calibration.readthedocs.io
