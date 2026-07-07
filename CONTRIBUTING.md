# Contributing

Thank you for considering contributing to CuraXYCalibration!

## Development Setup

```bash
git clone https://github.com/cura-xy-calibration/CuraXYCalibration.git
cd CuraXYCalibration
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test,docs]"
pre-commit install
```

## Code Standards

- Python 3.12+
- Full type annotations everywhere
- Google-style docstrings
- Follow SOLID principles
- No global mutable state
- Tests for all new code

## Workflow

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Make changes with tests.
4. Run `ruff check .`, `black --check .`, `mypy src/`.
5. Run `pytest` — all tests must pass.
6. Commit using conventional commits.
7. Push and open a Pull Request.

## Pull Request Checklist

- [ ] Code compiles and type-checks
- [ ] Tests pass with full coverage
- [ ] Documentation updated
- [ ] Lint passes (`ruff check .`)
- [ ] Format passes (`black --check .`)
- [ ] Security scan passes (`bandit -c pyproject.toml -r src/`)

## Commit Messages

Use [conventional commits](https://www.conventionalcommits.org/):

```
feat: add bilinear interpolation
fix: correct mesh boundary clamping
docs: update calibration guide
test: add profile serialization tests
```

## Code of Conduct

All contributors must abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
