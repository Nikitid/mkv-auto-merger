# Repository map

Where things live. The application is one 616-line Python script, so there is
no generated index; read the section you need.

## The shape of it

A command-line utility that prepares tracker-style anime and TV folders for
Jellyfin: it matches external dubbed audio to episodes, remuxes MKV containers
and produces a clean season structure.

| file | owns |
| --- | --- |
| `scripts/mkv-auto-merge.py` | the whole application |
| `tests/test_mkv_auto_merge_script.py` | the pytest suite |
| `scripts/setup.sh` | development environment |
| `scripts/lint.sh`, `scripts/test.sh` | the checks |
| `pyproject.toml` | package metadata and tool configuration |

## The parts that need care

File discovery, episode matching, collision handling and remux output are
where a mistake moves or deletes the wrong file. The tool cannot undo either,
so those paths get the tests.

## Checks

```sh
./scripts/lint.sh
./scripts/test.sh
```

## Documentation

| file | for |
| --- | --- |
| `AGENTS.md` | the rules of working here |
| `docs/MAP.md` | this file |
| `README.md` | operator-facing, Russian |
| `README.en.md` | the English version |
