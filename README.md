# MeshDeWarper

> Full XY distortion calibration plugin for Ultimaker Cura.

Characterize and compensate for non-linear positioning errors across the entire
printable area of your 3D printer. Warp G-code before export to correct XY
distortion with sub-millimeter precision.

## Features

- **Calibration Pattern Generator** — print reference grids as PDF / SVG / STL
- **G-Code Warping Engine** — full AST parser, format-preserving output
- **Multiple Interpolation Algorithms** — bilinear, bicubic, thin plate splines, RBF
- **Heatmap & Vector Field Visualization** — see distortion at a glance
- **Calibration Profile Manager** — save and load profiles
- **Experimental Computer Vision Assistant** — detect printed points from photos

## Installation

1. Download the latest `.curaplugin` from [Releases][releases].
2. In Cura, go to **Extensions → Manage Plugins**.
3. Click **Install from file** and select the downloaded package.
4. Restart Cura.

## Quick Start

```python
from pathlib import Path
from mesh_de_warper.core import Calibration
from mesh_de_warper.gcode.warper import GCodeWarper
from mesh_de_warper.interpolation import BilinearInterpolation

# Create a calibration grid
cal = Calibration.for_bed(
    width=220, height=220, spacing=10,
    interpolation=BilinearInterpolation(),
)

# Warp G-code
warper = GCodeWarper(cal)
warper.warp_file(Path("input.gcode"), Path("output.gcode"))
```

## Documentation

Full documentation is available on the [GitHub repository][repo].

## Development

```bash
git clone https://github.com/Jofralso/MeshDeWarper.git
cd MeshDeWarper
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,test]"
pre-commit install
pytest
```

## License

AGPL-3.0-only — see [LICENSE](LICENSE).

[releases]: https://github.com/Jofralso/MeshDeWarper/releases
[repo]: https://github.com/Jofralso/MeshDeWarper
