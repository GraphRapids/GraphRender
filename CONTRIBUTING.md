# Contributing

Thanks for contributing to GraphRender.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Running Checks

Run tests:

```bash
python -m pytest
```

Run compile sanity check:

```bash
python -m py_compile main.py src/graphrender/__init__.py src/graphrender/graphrender.py
```

## Project Structure

- `src/graphrender/`: library code
- `main.py`: CLI entrypoint
- `tests/`: pytest suite
- `.github/workflows/`: CI and security workflows

## Pull Requests

Before opening a PR:

1. Keep changes focused and atomic.
2. Add or update tests for behavioral changes.
3. Update docs (`README.md`, `THIRD_PARTY_NOTICES.md`, `CHANGELOG.md`) when relevant.
4. Ensure CI is green.

## Commit Guidance

- Use clear, imperative commit messages.
- Reference issue numbers when applicable.
- Avoid bundling unrelated changes in one PR.

## Reporting Bugs and Requesting Features

Use GitHub issue templates:

- Bug report
- Feature request

For security issues, follow `SECURITY.md`.
