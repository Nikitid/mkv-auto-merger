# Repository Guidelines

## Scope

This repository contains a Python command-line utility for reorganizing media
files and remuxing MKV containers for Jellyfin.

## Structure

- `scripts/mkv-auto-merge.py` — application entry point.
- `tests/` — pytest test suite.
- `scripts/lint.sh`, `scripts/test.sh`, `scripts/setup.sh` — development tasks.
- `pyproject.toml` — package metadata and tool configuration.

## Working rules

- Keep the standalone-script workflow and avoid broad architecture changes.
- Treat file discovery, episode matching, collision handling, remux output,
  move, and delete paths as data-sensitive.
- Never weaken dry-run behavior or overwrite protection without explicit
  requirements and tests.
- Keep repository documentation concise and neutral. Do not add marketing
  language or automation-tool attribution.
- Do not commit media files, generated output, local environments, or logs.

## Validation

```bash
make lint
make test
```

For file-operation changes, add or update tests covering dry run, collisions,
and source-file handling. Report any checks skipped because local tools are
unavailable.
