# Development

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Python 3.10 or newer: the script uses `X | None` annotations.

## Checks

```bash
make lint
make test
```

`scripts/lint.sh` is what CI runs: ShellCheck, shfmt, Python syntax, ruff and
the README layout.

## Release

Push a `vX.Y.Z` tag matching `version` in `pyproject.toml`. The release
workflow runs the tests and publishes notes made by `scripts/release-notes.sh`
from the commit subjects since the previous tag.
