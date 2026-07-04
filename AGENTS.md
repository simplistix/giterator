# Agent Instructions

## Principles

- **Done means green**: a change is only complete when `./happy.sh` exits 0; do not commit until it does.
- **No unrelated failures**: if `./happy.sh` fails on something unrelated to your changes, do NOT assume it is a pre-existing problem and proceed anyway. Stop immediately and ask the user how to proceed.
- **Docs for everything public**: new functionality or public API changes must have accompanying docs in `docs/*.rst`
- **No em-dashes or parenthetical asides in prose**: in `docs/*.rst` prose and Python docstrings, never use em-dashes, and never tuck a clause inside parentheses; rephrase with commas or separate sentences. This does not apply to code comments or agent-facing notes such as this file, where both are fine.
- **No stacked headings in docs**: a heading in `docs/*.rst` must be followed by prose, never immediately by a sub-heading. Add a short lead-in or merge the levels.
- **Type-annotate public APIs**: all public functions and classes need type annotations; mypy is the gate
- **Use `compare()` in tests**: assert with `compare(actual, expected=...)`, using `StringComparison` for pattern matches. Bare `assert` only for booleans and `isinstance` (which type-narrows for mypy).
- **No `noqa`, ever**: this project has zero linter suppressions; don't add them. Fix the underlying issue instead.
- **No `docs/changes.rst` edits during development**: that file is updated at release time, not as part of feature work.

## Project Overview

Giterator is a Python library and command line tool for doing git things: it wraps
command-line git to script repository operations and provides helpers for making
sample repositories in tests.

## Environment

```bash
uv sync --all-extras --all-groups              # setup or after pulling
rm -rf .venv && uv sync --all-extras --all-groups  # full reset
```

## Commands

```bash
./happy.sh                                     # all checks: required before commit
uv run pytest                                  # all tests
uv run pytest tests/test_git.py                # single file
uv run pytest --cov --cov-report=term-missing  # with coverage
uv run mypy src tests                          # type checking
uv run make -C docs html                       # build docs
uv build                                       # build sdist + wheel
```

## Architecture

`src/giterator/`: all source. Key modules:

- `git.py`: `Git`, the main class wrapping command-line git; also `User` and `GitError`
- `testing.py`: `Repo`, for making sample repositories in tests
- `clock.py`: controllable time source used for commit timestamps
- `cli.py`: the `giterator` command line entry point
- `__main__.py`: `python -m giterator` support
- `typing.py`: type definitions

Config: `pyproject.toml`.

Testing specifics:

- Coverage must be 100% and tracks both `giterator` and `tests`.
- CLI tests run `python -m giterator` in subprocesses: `tests/conftest.py` sets
  `COVERAGE_PROCESS_START` and the `coverage-enable-subprocess` dev dependency measures
  them, so coverage runs in parallel mode.
- Tests exercise real git via temporary repositories, so a `git` binary is required.
