# Agent Instructions

## Principles

- **Done means green** — a change is only complete when `./happy.sh` exits 0; do not commit until it does. If `./happy.sh` was already failing before your changes, you must fix those pre-existing failures too — or stop and ask the user how to proceed.
- **Docs for everything public** — new functionality or public API changes must have accompanying docs in `docs/*.rst`
- **Type-annotate public APIs** — all public functions and classes need type annotations; mypy is the gate

## Project Overview

Giterator is a Python library and command line tool for doing git things: it wraps
command-line git to script repository operations, and provides helpers for making
sample repositories in tests.

## Environment

```bash
uv sync --all-extras --all-groups              # setup or after pulling
rm -rf .venv && uv sync --all-extras --all-groups  # full reset
```

## Commands

```bash
./happy.sh                                          # all checks — required before commit
uv run pytest                                       # all tests
uv run pytest tests/test_git.py                     # single file
uv run pytest --cov --cov-report=term-missing       # with coverage
uv run mypy src tests                               # type checking
uv run make -C docs html                            # build docs
uv build                                            # build sdist + wheel
```

## Architecture

`src/giterator/` — all source. Key modules:

- `git.py` — `Git`, the main class wrapping command-line git; also `User` and `GitError`
- `testing.py` — `Repo`, for making sample repositories in tests
- `clock.py` — controllable time source used for commit timestamps
- `cli.py` — the `giterator` command line entry point
- `__main__.py` — `python -m giterator` support
- `typing.py` — type definitions

Config: `pyproject.toml`.

## Notes

- Coverage tracks both `giterator` package and `tests` directory, and must be 100%
- CLI tests in `tests/test_cli.py` run `python -m giterator` in a subprocess;
  `tests/conftest.py` sets `COVERAGE_PROCESS_START` and the `coverage-enable-subprocess`
  dev dependency makes sure those subprocesses are measured — coverage runs in
  parallel mode as a result
- Tests exercise real git via temporary repositories, so a `git` binary is required
