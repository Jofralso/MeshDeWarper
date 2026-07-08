Testing Guide
=============

Running Tests
-------------

Install test dependencies and run the full suite:

.. code-block:: bash

   pip install -e ".[test]"
   pytest

Run with coverage:

.. code-block:: bash

   pytest --cov=mesh_de_warper --cov-report=term-missing

Run specific test categories:

.. code-block:: bash

   pytest tests/unit/           # Unit tests only
   pytest tests/integration/    # Integration tests only
   pytest -m interpolation      # Interpolation algorithm tests
   pytest -m gcode              # G-code pipeline tests
   pytest -m vision             # Computer vision tests

Test Structure
--------------

Tests are organised in two directories:

``tests/unit/``
    Accuracy and edge-case tests for interpolation algorithms.
    These validate that offsets are computed correctly across various
    mesh configurations.

``tests/integration/``
    End-to-end tests of the G-code pipeline (parse → warp → emit) and
    full calibration round-trips.

Top-level test files align with source modules:

* ``test_point.py`` — ``Point`` dataclass
* ``test_mesh.py`` — ``Mesh`` grid operations
* ``test_calibration.py`` — ``Calibration`` orchestrator
* ``test_profile.py`` — ``CalibrationProfile`` serialisation
* ``test_gcode_*.py`` — parser, AST, emitter, warper
* ``test_*_interpolation.py`` — each interpolation algorithm
* ``test_patterns.py`` — pattern generators
* ``test_vision.py`` — vision assistant
* ``test_visualization.py`` — heatmap, vector field, preview
* ``test_plugin.py`` — Cura plugin entry point

Writing Tests
-------------

Follow these conventions when adding tests:

1. Place tests in the appropriate file or create a new ``test_*.py``
   in ``tests/``.
2. Use the ``temp_dir`` fixture from ``conftest.py`` for file I/O tests.
3. Use descriptive test function names prefixed with ``test_``.
4. Add pytest markers for slow, vision, or integration tests.

Example:

.. code-block:: python

   import pytest
   from mesh_de_warper.core.mesh import Mesh

   def test_mesh_initialisation() -> None:
       mesh = Mesh(width=100, height=100, spacing=10)
       assert mesh.num_points == 121  # 11 × 11 grid
       assert mesh[0, 0].offset_x == 0.0

Continuous Integration
----------------------

The CI pipeline (``.github/workflows/ci.yml``) runs on every push and
pull request:

* Lint with Ruff
* Type-check with mypy
* Run all tests with coverage
* Security audit with bandit and pip-audit
* Build and smoke-test the package

Coverage
--------

Aim for at least 90% code coverage. The coverage configuration in
``pyproject.toml`` excludes ``__repr__``, ``__str__``, and
``NotImplementedError`` lines from coverage requirements.
