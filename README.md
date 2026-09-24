# MKV Auto Merger for Jellyfin

[Русский](README.ru.md)

[![CI](https://github.com/Nikitid/mkv-auto-merger/actions/workflows/lint.yml/badge.svg)](https://github.com/Nikitid/mkv-auto-merger/actions/workflows/lint.yml)
[![Release](https://img.shields.io/github/v/release/Nikitid/mkv-auto-merger)](https://github.com/Nikitid/mkv-auto-merger/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Command-line utility for preparing TV series and anime folders for Jellyfin.
It finds video files, matches external audio tracks, remuxes with `mkvmerge`
when needed, and creates a `Season XX` directory structure.

## Features

- recursive scanning of tracker-style folders;
- multiple external audio tracks;
- support for `Sounds`, `Sound`, `audio`, `DUB`, `voice`, `озвучка`,
  `звук`, and `аудио` directories;
- fast move path when no additional audio is found;
- season, bonus, OVA, OAD, and special episode detection;
- embedded subtitle removal during remux; external subtitles are not added;
- Jellyfin-compatible `SxxExx` naming;
- change preview without modifying files.

## Requirements

- Python 3.12 or newer;
- `mkvmerge` from MKVToolNix;
- for development: `pytest`, `ruff`, `shellcheck`, and `shfmt`.

macOS:

```bash
brew install mkvtoolnix shellcheck shfmt
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y mkvtoolnix shellcheck shfmt python3 python3-venv
```

## Installation

```bash
git clone https://github.com/Nikitid/mkv-auto-merger.git
cd mkv-auto-merger
python3 scripts/mkv-auto-merge.py /path/to/work-folder
```

## Usage

Minimal source layout:

```text
Work folder/
  Title S01/
    01.mkv
    Sounds/Studio/01.mka
    Bonus/01.mkv
```

Expected output:

```text
Work folder/
  Title/
    Season 00/
      Title - S00E01.mkv
    Season 01/
      Title - S01E01.mkv
```

Recommended menu order:

```text
4) DRY RUN
1) MERGE
6) MOVE TO LIBRARY
```

Main menu actions:

- `MERGE` - assemble episodes and add matched audio tracks;
- `RENAME` - apply Jellyfin-compatible names;
- `CLEANUP` - remove empty directories;
- `FINAL CONSOLIDATE` - combine detected seasons;
- `MOVE TO LIBRARY` - move output to the configured media library;
- `DELETE EXTERNAL SUBS` - remove external subtitle files.

`MERGE` offers three source-video modes:

- `m` - move; the default;
- `k` - keep source files;
- `d` - delete source video after successful processing.

Review the `DRY RUN` plan and keep a backup before using modes that move or
delete files.

## Data safety

The tool works on a user media library and can move or delete source files.
Check the paths before running it, start with a dry run, and keep a backup: it
cannot undo a move or a deletion.

## Development

```sh
make lint test
```

Setup, checks and releasing: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Documentation

- [Repository map](docs/MAP.md) - where things live
- [Development](docs/DEVELOPMENT.md) - setup, checks and releasing

## Support

Questions and bug reports go to
[Issues](https://github.com/Nikitid/mkv-auto-merger/issues/new/choose): pick the form that
fits. Report a vulnerability privately through
[a security advisory](https://github.com/Nikitid/mkv-auto-merger/security/advisories/new).
English or Russian is fine.

## License

[MIT](LICENSE)
