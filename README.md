# MKV Auto Merger

Prepare anime and TV series folders from trackers for Jellyfin.

The script scans messy release folders, finds video files, matches external dubbed audio from one or more studios, strips subtitles, and writes a Jellyfin-friendly structure:

```text
Title/
  Season 01/
    Title - S01E01.mkv
  Season 00/
    Title - S00E01.mkv
```

## Features

- Recursive scan of tracker-style folders.
- Multiple audio studios merged into one MKV as separate audio tracks.
- External subtitles are ignored.
- Embedded subtitles are removed with `mkvmerge --no-subtitles`.
- Bonus, OVA, OAD, specials, and extras go to `Season 00`.
- Season folders like `Title S01`, `Title Season 1`, `Title/Season 1` are supported.
- Audio folders like `Sounds`, `Sound`, `audio`, `DUB`, `voice`, `озвучка`, `звук`, `аудио` are supported.
- Dry-run mode shows the full plan before files are changed.

## Requirements

- Python 3.12+
- `mkvmerge` from MKVToolNix
- Optional development tools: `pytest`, `ruff`, `shellcheck`, `shfmt`

macOS:

```bash
brew install mkvtoolnix shellcheck shfmt
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y mkvtoolnix shellcheck shfmt python3 python3-venv
```

## Quick Use From GitHub

Replace the URL with your repository URL after publishing:

```bash
git clone https://github.com/<user>/mkv-auto-merger.git
cd mkv-auto-merger
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/mkv-auto-merge.py /path/to/work-folder
```

Inside the menu, use this order:

```text
4) DRY RUN
1) MERGE
6) MOVE TO LIBRARY
```

## Expected Folder Layout

Minimum:

```text
Work folder/
  Title S01/
    01.mkv
    Sounds/Studio/01.mka
    Bonus/01.mkv
```

Also supported:

```text
Work folder/
  Title S01/
    [Tracker] Title S01E01 1080p.mkv
    DUB/AniLibria/Title 01.flac
    Озвучка/StudioBand/01.dts
    Specials/OVA 01.mkv

  Title S02/
    01.mkv
    Sounds/AniLibria/01.mka
```

Output:

```text
Work folder/
  Title/
    Season 00/
      Title - S00E01.mkv
    Season 01/
      Title - S01E01.mkv
    Season 02/
      Title - S02E01.mkv
```

## Menu

```text
1) MERGE: Собрать серии
2) RENAME: Jellyfin SxxExx
3) CLEANUP: Удалить пустые папки
4) DRY RUN: План работ
5) FINAL CONSOLIDATE: Склеить сезоны
6) MOVE TO LIBRARY: Перенести в /data/anime
7) DELETE EXTERNAL SUBS: удалить .ass/.srt/.ssa
8) EXIT: Выход
```

`MERGE` asks what to do with original video files:

- `k` / keep: keep source files.
- `m` / move: move source videos to `Originals/`.
- `d` / delete: delete source videos after a successful merge.

Use `DRY RUN` before `MERGE`. It shows every video, matched audio tracks, ignored subtitles, and output path.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
make lint
make test
```

## GitHub Publishing

From this project directory:

```bash
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/<user>/mkv-auto-merger.git
git push -u origin main
```

## License

Released under the MIT license.
