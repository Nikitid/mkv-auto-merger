# MKV Auto Merger

[English](README.en.md)

[![Лицензия: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Проверки](https://github.com/Nikitid/mkv-auto-merger/actions/workflows/lint.yml/badge.svg)](https://github.com/Nikitid/mkv-auto-merger/actions/workflows/lint.yml)

Консольный инструмент для подготовки папок с сериалами и аниме к импорту в
Jellyfin. Скрипт находит видео, сопоставляет внешние аудиодорожки, при
необходимости выполняет remux через `mkvmerge` и создает структуру
`Season XX`.

## Состояние

Проект используется как самостоятельный скрипт. Актуальная версия пакета —
`0.1.0`. Перед операциями с файлами рекомендуется сначала запускать сухой
прогон.

## Возможности

- рекурсивный поиск видео в папках раздач;
- добавление нескольких внешних аудиодорожек;
- поддержка папок `Sounds`, `Sound`, `audio`, `DUB`, `voice`, `озвучка`,
  `звук` и `аудио`;
- перенос без remux, если дополнительное аудио не найдено;
- распознавание сезонов, бонусов, OVA, OAD и специальных выпусков;
- удаление встроенных субтитров при remux; внешние субтитры не добавляются;
- переименование в формат Jellyfin `SxxExx`;
- предварительный план без изменения файлов.

## Требования

- Python 3.12 или новее;
- `mkvmerge` из MKVToolNix;
- для разработки: `pytest`, `ruff`, `shellcheck` и `shfmt`.

macOS:

```bash
brew install mkvtoolnix shellcheck shfmt
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y mkvtoolnix shellcheck shfmt python3 python3-venv
```

## Установка

```bash
git clone https://github.com/Nikitid/mkv-auto-merger.git
cd mkv-auto-merger
python3 scripts/mkv-auto-merge.py /path/to/work-folder
```

## Использование

Минимальная исходная структура:

```text
Work folder/
  Title S01/
    01.mkv
    Sounds/Studio/01.mka
    Bonus/01.mkv
```

Ожидаемый результат:

```text
Work folder/
  Title/
    Season 00/
      Title - S00E01.mkv
    Season 01/
      Title - S01E01.mkv
```

Рекомендуемый порядок действий в меню:

```text
4) DRY RUN
1) MERGE
6) MOVE TO LIBRARY
```

Основные пункты меню:

- `MERGE` — собрать серии и добавить найденные аудиодорожки;
- `RENAME` — привести имена к формату Jellyfin;
- `CLEANUP` — удалить пустые каталоги;
- `FINAL CONSOLIDATE` — объединить найденные сезоны;
- `MOVE TO LIBRARY` — перенести результат в настроенную медиатеку;
- `DELETE EXTERNAL SUBS` — удалить внешние файлы субтитров.

При `MERGE` доступны три режима для исходного видео:

- `m` — переместить; режим по умолчанию;
- `k` — оставить исходные файлы;
- `d` — удалить исходное видео после успешной обработки.

Проверьте план `DRY RUN` и резервную копию перед режимами, которые перемещают
или удаляют файлы.

## Разработка

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
make lint
make test
```

## Безопасность данных

Инструмент работает с пользовательской медиатекой и может перемещать или
удалять исходные файлы. Подробности приведены в [SECURITY.md](SECURITY.md).

## Лицензия

[MIT](LICENSE)
