Release Guide
=============

This document describes the release process for MeshDeWarper.

Versioning
----------

The project follows `Semantic Versioning <https://semver.org/>`_:

* **MAJOR** — breaking API changes
* **MINOR** — new features, no breaking changes
* **PATCH** — bug fixes and minor improvements

The current version is ``0.1.0`` (alpha).

Release Process
---------------

1. **Update the version**

   Edit ``src/mesh_de_warper/__version__.py``:

   .. code-block:: python

      __version__: Final[str] = "0.2.0"
      __version_info__: Final[tuple[int, int, int]] = (0, 2, 0)

   Also update ``version`` in ``setup.cfg`` and ``pyproject.toml``.

2. **Update the changelog**

   Ensure all notable changes are documented. The release drafter
   workflow (``.github/release-drafter.yml``) can help generate
   release notes automatically.

3. **Run the full test suite**

   .. code-block:: bash

      pytest --cov=mesh_de_warper
      ruff check src/
      mypy src/

4. **Create a release commit**

   .. code-block:: bash

      git add -A
      git commit -m "Release v0.2.0"

5. **Tag the release**

   .. code-block:: bash

      git tag -a v0.2.0 -m "v0.2.0"
      git push origin v0.2.0

6. **CI/CD automation**

   Pushing a tag triggers ``.github/workflows/release.yml`` which:

   * Builds the ``.curaplugin`` package
   * Publishes to PyPI
   * Creates a GitHub Release with release notes
   * Builds and deploys documentation to GitHub Pages

Post-Release
------------

* Verify the PyPI package installs correctly:

  .. code-block:: bash

     pip install MeshDeWarper

* Verify the documentation is deployed at
  https://mesh-de-warper.readthedocs.io
* Monitor for any issues reported on the
  `issue tracker <https://github.com/mesh-de-warper/MeshDeWarper/issues>`_.

Hotfix Releases
---------------

For critical bug fixes, create a patch release from the same major.minor
branch:

.. code-block:: bash

   git checkout v0.2.x
   git cherry-pick <fix-commit>
   git tag -a v0.2.1 -m "v0.2.1"
   git push origin v0.2.1
