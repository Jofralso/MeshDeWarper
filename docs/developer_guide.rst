Developer Guide
===============

This guide covers the project architecture, key modules, and
contribution workflow for developers.

Project Structure
-----------------

::

   src/mesh_de_warper/
   ├── __init__.py         # Public API re-exports
   ├── __version__.py      # Version string
   ├── plugin.py           # Cura plugin entry point
   ├── core/               # Core data types
   │   ├── point.py        #   2D point with offset
   │   ├── mesh.py         #   Rectangular grid of points
   │   ├── calibration.py  #   Calibration orchestrator
   │   └── profile.py      #   Serialisable profile
   ├── gcode/              # G-code processing pipeline
   │   ├── ast.py          #   G-code AST data types
   │   ├── parser.py       #   Text-to-AST
   │   ├── emitter.py      #   AST-to-text
   │   └── warper.py       #   Distortion correction engine
   ├── interpolation/      # Interpolation algorithms
   │   ├── base.py         #   Abstract base class
   │   ├── bilinear.py     #   Bilinear interpolation
   │   ├── bicubic.py      #   Bicubic (Catmull-Rom)
   │   ├── tps.py          #   Thin plate spline
   │   └── rbf.py          #   Radial basis function
   ├── patterns/           # Calibration pattern generators
   │   ├── base.py         #   Config and abstract generator
   │   ├── pdf_generator.py
   │   ├── svg_generator.py
   │   └── stl_generator.py
   ├── vision/             # Computer vision assistant
   │   ├── detection.py    #   Point detection (OpenCV)
   │   ├── correction.py   #   Lens & perspective correction
   │   └── calibration.py  #   Vision calibration workflow
   ├── visualization/      # Distortion visualisation
   │   ├── heatmap.py      #   Offset magnitude heatmap
   │   ├── vector_field.py #   Offset vector quiver plot
   │   └── preview.py      #   Combined overlay
   └── ui/                 # PyQt5 calibration editor
       ├── editor.py       #   Main editor widget
       └── profile_manager.py

Core Design Principles
----------------------

1. **Stateless interpolation** — all ``InterpolationAlgorithm``
   implementations are stateless, enabling caching and parallel evaluation.
   The interpolation result depends only on the mesh and query point.

2. **Format-preserving G-code** — the G-code pipeline parses to a full AST,
   warps only XY coordinates in movement commands, and re-emits without
   altering comments, line numbers, word order, or formatting.

3. **Graceful degradation** — optional dependencies (PyQt5, OpenCV,
   scikit-image) are imported inside try/except blocks. Missing libraries
   disable the corresponding feature rather than breaking the entire
   package.

4. **Separation of concerns** — core data types have no dependency on
   visualisation, UI, or G-code modules.

Adding a New Interpolation Algorithm
-------------------------------------

1. Create a new module in ``src/mesh_de_warper/interpolation/``.
2. Subclass ``InterpolationAlgorithm`` and implement ``interpolate()``
   and ``name()``.
3. Register it in ``src/mesh_de_warper/interpolation/__init__.py``.
4. Add unit tests in ``tests/``.
5. Add accuracy tests in ``tests/unit/test_interpolation_accuracy.py``.

Code Quality
------------

The project uses strict quality checks configured in ``pyproject.toml``:

* **Ruff** — linting and formatting (``ruff check . && ruff format .``)
* **Mypy** — strict static typing (``mypy src/``)
* **Pytest** — 200+ tests with coverage (``pytest --cov=mesh_de_warper``)
* **Bandit** — security scanning (``bandit -r src/``)

All checks are enforced in CI (``.github/workflows/ci.yml``).
