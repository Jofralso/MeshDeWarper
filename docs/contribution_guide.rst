Contribution Guide
==================

Thank you for considering contributing to MeshDeWarper!

Code of Conduct
---------------

This project follows the `Contributor Covenant <https://www.contributor-covenant.org/>`_
Code of Conduct. By participating, you agree to abide by its terms.
See ``CODE_OF_CONDUCT.md`` for the full text.

Getting Started
---------------

1. Fork the repository on GitHub.
2. Clone your fork:

   .. code-block:: bash

      git clone https://github.com/your-username/MeshDeWarper.git
      cd MeshDeWarper

3. Create a virtual environment and install dependencies:

   .. code-block:: bash

      python -m venv .venv
      source .venv/bin/activate
      pip install -e ".[dev,test]"
      pre-commit install

4. Create a feature branch:

   .. code-block:: bash

      git checkout -b feature/my-feature

What to Work On
---------------

* **Bug fixes** — check the `issue tracker`_ for open bugs.
* **New features** — discuss your idea in a GitHub issue first.
* **Documentation** — improvements to docs, docstrings, and tutorials.
* **Test coverage** — add tests for untested code paths.

Pull Request Guidelines
-----------------------

1. **One PR per feature or bug fix** — keep changes focused.
2. **Write tests** — cover new code with unit and/or integration tests.
3. **Maintain style** — the project uses Ruff for linting and formatting:

   .. code-block:: bash

      ruff check src/ tests/
      ruff format src/ tests/

4. **Type-check** — all code must pass mypy strict mode:

   .. code-block:: bash

      mypy src/

5. **Pass CI** — ensure all checks pass on GitHub Actions.
6. **Update documentation** — if your change affects the public API,
   update the relevant RST docs and the API reference.

Commit Messages
---------------

Write clear, concise commit messages:

.. code-block:: text

   module: brief description

   Longer explanation if needed. Wrap at 72 characters.

   Fixes #123

Examples:

* ``gcode: handle G2 arcs with zero radius``
* ``interpolation: add inverse distance weighting algorithm``
* ``docs: fix typo in calibration guide``

Review Process
--------------

1. Maintainers review the PR within a few days.
2. Address any feedback with additional commits.
3. Once approved, a maintainer merges the PR.

.. _issue tracker: https://github.com/mesh-de-warper/MeshDeWarper/issues
