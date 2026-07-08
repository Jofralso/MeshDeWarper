# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Report security vulnerabilities to security@mesh-de-warper.dev.

Do **not** file public GitHub issues for security vulnerabilities.

You should receive a response within 48 hours. If the issue is confirmed,
a patch will be released as soon as possible.

## Security Practices

- All dependencies are pinned and audited via `pip-audit` and `safety`.
- Code is scanned with `bandit` on every commit.
- No secrets or credentials are ever committed to the repository.
- Secrets are managed via environment variables or external secret stores.
