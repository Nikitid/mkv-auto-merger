#!/usr/bin/env python3
import argparse
import re
import shutil
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

# --- Настройки ---
VIDEO_EXTS = {".mkv", ".mp4", ".mov", ".avi", ".m4v"}
AUDIO_EXTS = {
    ".mka",
    ".flac",
    ".ogg",
    ".opus",
    ".mp3",
    ".aac",
    ".m4a",
    ".ac3",
    ".eac3",
    ".dts",
    ".thd",
    ".wav",
}
SUB_EXTS = {".ass", ".srt", ".ssa", ".sub", ".idx", ".vtt"}
AUDIO_PRIORITY = [".mka", ".flac", ".thd", ".dts", ".ac3", ".eac3", ".opus", ".mp3"]
DEST_LIBRARY = Path("/data/anime")

AUDIO_DIR_NAMES = {
    "audio",
    "audios",
    "sound",
    "sounds",
    "dub",
    "dubs",
    "voice",
    "voices",
    "озвучка",
    "звук",
    "аудио",
}
BONUS_DIR_NAMES = {"bonus", "bonuses", "special", "specials", "ova", "oad", "extra", "extras"}
OUTPUT_DIR_NAMES = {"originals"}
TECH_TOKENS = {"480", "720", "1080", "1440", "2160", "264", "265", "10", "8"}


@dataclass(frozen=True)
class MediaRef:
    path: Path
    season: int
    episode: int | None
    is_bonus: bool = False


@dataclass(frozen=True)
class EpisodePlan:
    title_dir: Path
    title: str
    video: MediaRef
    audios: tuple[tuple[str, Path], ...]
    output_file: Path
    ignored_subtitles: tuple[Path, ...]


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    for i in range(1, 1000):
        candidate = path.with_name(f"{path.stem} ({i}){path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Too many duplicate names for {path}")


def move_path(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    safe_dest = unique_path(dest)
    shutil.move(str(src), str(safe_dest))
    return safe_dest


def copy_path(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    safe_dest = unique_path(dest)
    shutil.copy2(src, safe_dest)
    return safe_dest


def normalized_name(value: str) -> str:
    return re.sub(r"[\s._-]+", " ", value.casefold()).strip()


def is_named_like(path: Path, names: set[str]) -> bool:
    normalized = normalized_name(path.name)
    return normalized in names or any(token in normalized.split() for token in names)


def is_work_folder(path: Path) -> bool:
    return (
        path.is_dir()
        and not path.name.startswith("Season")
        and normalized_name(path.name) not in {"data anime", "originals"}
    )


def is_output_path(path: Path) -> bool:
    return any(normalized_name(part) in OUTPUT_DIR_NAMES for part in path.parts)


def is_audio_dir(path: Path) -> bool:
    return is_named_like(path, AUDIO_DIR_NAMES)


def is_bonus_path(path: Path) -> bool:
    return any(is_named_like(parent, BONUS_DIR_NAMES) for parent in path.parents)


def clean_title(folder_name: str) -> str:
    cleaned = re.sub(
        r"\s*(?:s|season|сезон)\s?\d{1,2}\s*$",
        "",
        folder_name,
        flags=re.IGNORECASE,
    )
    return cleaned.strip(" ._-") or folder_name


def print_welcome() -> None:
    print("\n" + "=" * 60)
    print("ANIME/SERIES JELLYFIN PREP")
    print("=" * 60)
    print("Что делает:")
    print("  1. Сканирует грязные папки раздач.")
    print("  2. Находит видео, озвучки разных студий и бонусы.")
    print("  3. Быстро переносит готовое или собирает MKV с озвучкой для Jellyfin.")
    print()
    print("Минимальная структура:")
    print("  Рабочая папка/")
    print("    Title S01/")
    print("      01.mkv")
    print("      Sounds/Studio/01.mka")
    print("      Bonus/01.mkv")
    print()
    print("Также понимает:")
    print("  Title/Season 1/01.mkv")
    print("  DUB/AniLibria/01.flac, Озвучка/Studio/01.dts")
    print("  Bonus, Bonuses, Specials, OVA, OAD -> Season 00")
    print()
    print("Итог:")
    print("  Title/Season 01/Title - S01E01.mkv")
    print("  Title/Season 00/Title - S00E01.mkv")
    print()
    print("Рекомендуемый порядок: 4) DRY RUN -> 1) MERGE -> 6) MOVE TO LIBRARY.")
    print("Без озвучки: быстрый move/rename без remux. С озвучкой: mkvmerge без субтитров.")
    print("=" * 60)


# --- Логика имен и поиска ---


def extract_season_num(path_name: str) -> str:
    match = re.search(r"(?:s|season|сезон)\s?(?P<num>\d{1,2})", path_name, re.IGNORECASE)
    if match:
        return f"{int(match.group('num')):02d}"
    return "01"


def extract_episode_num(name: str) -> int | None:
    patterns = [
        r"[sS]\d{1,2}\s*[eE](?P<ep>\d{1,3})",
        r"(?<!\d)\d{1,2}[xX](?P<ep>\d{1,3})(?!\d)",
        r"(?:ep|episode|серия|серии)\s*\.?\s*(?P<ep>\d{1,3})(?!\d)",
        r"(?:^|[\s._\-\[\(])(?P<ep>\d{1,3})(?:v\d+)?(?:$|[\s._\-\]\)])",
    ]
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if not match:
            continue
        episode = int(match.group("ep"))
        if 0 < episode < 200:
            return episode

    candidates = []
    for raw in re.findall(r"(?<![a-zA-Zа-яА-Я])(\d{1,3})(?!\d)", name):
        if raw in TECH_TOKENS:
            continue
        episode = int(raw)
        if 0 < episode < 200:
            candidates.append(episode)
    return candidates[-1] if candidates else None


def extract_ep_num(name: str) -> str | None:
    episode = extract_episode_num(name)
    return str(episode) if episode is not None else None


def extract_season_from_path(path: Path, default: int = 1) -> int:
    for part in reversed(path.parts):
        match = re.search(r"(?:s|season|сезон)\s?(?P<num>\d{1,2})", part, re.IGNORECASE)
        if match:
            return int(match.group("num"))
    return default


def collect_files(root: Path, extensions: set[str]) -> list[Path]:
    return sorted(
        [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in extensions and not is_output_path(path)
        ]
    )


def collect_videos(title_dir: Path) -> list[MediaRef]:
    default_season = int(extract_season_num(title_dir.name))
    videos = []
    for path in collect_files(title_dir, VIDEO_EXTS):
        is_bonus = is_bonus_path(path)
        season = (
            0
            if is_bonus
            else extract_season_from_path(path.relative_to(title_dir), default_season)
        )
        videos.append(
            MediaRef(
                path=path,
                season=season,
                episode=extract_episode_num(path.stem),
                is_bonus=is_bonus,
            )
        )
    return sorted(videos, key=lambda item: (item.season, item.episode or 999, str(item.path)))


def infer_studio(title_dir: Path, audio: Path) -> str:
    rel_parts = audio.relative_to(title_dir).parts
    for index, part in enumerate(rel_parts[:-1]):
        if is_audio_dir(Path(part)):
            if index + 1 < len(rel_parts) - 1:
                return rel_parts[index + 1].strip() or "Default"
            return "Default"
    return audio.parent.name if audio.parent != title_dir else "Default"


def audio_sort_key(path: Path) -> tuple[int, str]:
    suffix = path.suffix.lower()
    priority = AUDIO_PRIORITY.index(suffix) if suffix in AUDIO_PRIORITY else 99
    return priority, path.name.casefold()


def find_audio_matches(title_dir: Path, video: MediaRef) -> list[tuple[str, Path]]:
    if video.episode is None:
        return []

    grouped: dict[str, list[Path]] = defaultdict(list)
    for audio in collect_files(title_dir, AUDIO_EXTS):
        if is_bonus_path(audio) != video.is_bonus:
            continue
        audio_episode = extract_episode_num(audio.stem)
        if audio_episode != video.episode:
            continue
        audio_season = extract_season_from_path(audio.relative_to(title_dir), video.season or 1)
        if video.season and audio_season not in {video.season, 1}:
            continue
        grouped[infer_studio(title_dir, audio)].append(audio)

    return [
        (studio, sorted(paths, key=audio_sort_key)[0])
        for studio, paths in sorted(grouped.items())
    ]


def find_ignored_subtitles(title_dir: Path, video: MediaRef) -> list[Path]:
    if video.episode is None:
        return []
    return [
        sub
        for sub in collect_files(title_dir, SUB_EXTS)
        if is_bonus_path(sub) == video.is_bonus and extract_episode_num(sub.stem) == video.episode
    ]


def output_base_for(title_dir: Path) -> Path:
    title = clean_title(title_dir.name)
    return title_dir if title == title_dir.name else title_dir.parent / title


def output_name(title: str, season: int, episode: int | None, fallback: str) -> str:
    if episode is None:
        return f"{fallback}.mkv"
    return f"{title} - S{season:02d}E{episode:02d}.mkv"


def build_episode_plan(title_dir: Path, video: MediaRef) -> EpisodePlan:
    title = clean_title(title_dir.name)
    season_dir = output_base_for(title_dir) / f"Season {video.season:02d}"
    output_file = season_dir / output_name(title, video.season, video.episode, video.path.stem)
    return EpisodePlan(
        title_dir=title_dir,
        title=title,
        video=video,
        audios=tuple(find_audio_matches(title_dir, video)),
        output_file=output_file,
        ignored_subtitles=tuple(find_ignored_subtitles(title_dir, video)),
    )


def get_episode_data(title_dir: Path, video: Path):
    video_ref = MediaRef(
        path=video,
        season=(
            0
            if is_bonus_path(video)
            else extract_season_from_path(video.relative_to(title_dir))
        ),
        episode=extract_episode_num(video.stem),
        is_bonus=is_bonus_path(video),
    )
    plan = build_episode_plan(title_dir, video_ref)
    return list(plan.audios), []


def build_plans(root: Path) -> list[EpisodePlan]:
    plans = []
    for folder in [path for path in root.iterdir() if is_work_folder(path)]:
        if folder.name.startswith("Season"):
            continue
        for video in collect_videos(folder):
            plan = build_episode_plan(folder, video)
            if video.path.resolve() == plan.output_file.resolve():
                continue
            plans.append(plan)
    return sorted(
        plans,
        key=lambda plan: (plan.title, plan.video.season, plan.video.episode or 999),
    )


# --- Процессор ---


def build_mkvmerge_command(plan: EpisodePlan) -> list[str]:
    cmd = [
        "mkvmerge",
        "-o",
        str(plan.output_file),
        "--no-date",
        "--disable-track-statistics-tags",
        "--no-subtitles",
        "(",
        str(plan.video.path),
        ")",
    ]
    for studio, audio in plan.audios:
        lang = "eng" if "crunchy" in studio.casefold() else "rus"
        cmd += [
            "--language",
            f"0:{lang}",
            "--track-name",
            f"0:{studio.strip()}",
            "(",
            str(audio),
            ")",
        ]
    return cmd


def process_plan(plan: EpisodePlan, keep_mode: str) -> str:
    plan.output_file.parent.mkdir(parents=True, exist_ok=True)

    if plan.output_file.exists() and plan.output_file.stat().st_size > 0:
        return f"SKIP: {plan.output_file.name}"

    if plan.video.episode is None:
        return f"WARN: no episode number, skipped {plan.video.path.name}"

    if not plan.audios:
        try:
            if keep_mode == "keep":
                out_file = copy_path(plan.video.path, plan.output_file)
                return f"FAST COPY: {out_file.name}"
            out_file = move_path(plan.video.path, plan.output_file)
            return f"FAST MOVE: {out_file.name}"
        except Exception as e:
            return f"ERR: {plan.video.path.name}: {e}"

    try:
        subprocess.run(build_mkvmerge_command(plan), check=True, capture_output=True)
        if keep_mode == "delete":
            plan.video.path.unlink()
        elif keep_mode == "move":
            move_path(plan.video.path, plan.title_dir / "Originals" / plan.video.path.name)
        return f"MUX DONE: {plan.output_file.name} (+{len(plan.audios)} aud)"
    except Exception as e:
        if plan.output_file.exists():
            plan.output_file.unlink()
        return f"ERR: {plan.video.path.name}: {e}"


def process_episode(title_dir: Path, video: Path, keep_mode: str) -> str:
    video_ref = MediaRef(
        path=video,
        season=(
            0
            if is_bonus_path(video)
            else extract_season_from_path(video.relative_to(title_dir))
        ),
        episode=extract_episode_num(video.stem),
        is_bonus=is_bonus_path(video),
    )
    return process_plan(build_episode_plan(title_dir, video_ref), keep_mode)


# --- Действия ---


def action_dry_run(root: Path) -> None:
    print("\n" + "=" * 60 + "\nDRY RUN: План обработки\n" + "=" * 60)
    plans = build_plans(root)
    if not plans:
        print("Пусто.")
        return

    for plan in plans:
        rel_video = plan.video.path.relative_to(plan.title_dir)
        label = "S00" if plan.video.is_bonus else f"S{plan.video.season:02d}"
        episode = f"E{plan.video.episode:02d}" if plan.video.episode else "E??"
        print(f"\n{plan.title} [{label}{episode}]")
        print(f"  video: {rel_video}")
        print(f"  out:   {plan.output_file}")
        if plan.audios:
            for studio, audio in plan.audios:
                print(f"  audio: {studio} -> {audio.relative_to(plan.title_dir)}")
        else:
            print("  audio: not found")
        if plan.ignored_subtitles:
            print(
                f"  subs:  ignored external x{len(plan.ignored_subtitles)}; "
                "embedded stripped only when remuxing"
            )
        else:
            print("  subs:  embedded stripped only when remuxing")
        action = "REMUX" if plan.audios else "FAST MOVE/COPY"
        print(f"  action: {action}")


def action_delete_external_subtitles(root: Path) -> None:
    subtitles = []
    for folder in [path for path in root.iterdir() if is_work_folder(path)]:
        subtitles.extend(collect_files(folder, SUB_EXTS))

    if not subtitles:
        print("Внешние субтитры не найдены.")
        return

    for sub in subtitles:
        sub.unlink()
        print(f"DEL SUB: {sub}")


def action_final_consolidate(root: Path) -> None:
    print("\n--- FINAL CONSOLIDATE: Объединение папок Sxx ---")
    anime_folders = {}
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        m = re.match(r"(.+?)\s*S(\d{2})$", folder.name, re.IGNORECASE)
        if m:
            title_base = m.group(1).strip()
            anime_folders.setdefault(title_base, []).append((int(m.group(2)), folder))

    for title, seasons in anime_folders.items():
        seasons.sort(key=lambda x: x[0])
        new_folder = root / title
        new_folder.mkdir(exist_ok=True)
        print(f"Сборка: {title}")

        for i, (old_num, folder) in enumerate(seasons, 1):
            old_s_dir = folder / f"Season {old_num:02d}"
            if not old_s_dir.exists():
                print(f"   Не найдена папка Season {old_num:02d} в {folder.name}")
                continue

            target_s_dir = new_folder / f"Season {i:02d}"
            target_s_dir.mkdir(exist_ok=True)

            for f in old_s_dir.iterdir():
                move_path(f, target_s_dir / f.name)

            try:
                shutil.rmtree(folder)
                print(f"   Сезон {old_num} -> Season {i:02d}")
            except Exception as e:
                print(f"   Ошибка удаления {folder.name}: {e}")


def action_move_to_library(root: Path) -> None:
    print(f"\n--- Перенос в {DEST_LIBRARY} ---")
    if not DEST_LIBRARY.exists():
        try:
            DEST_LIBRARY.mkdir(parents=True, exist_ok=True)
        except Exception:
            print(f"Ошибка доступа к {DEST_LIBRARY}")
            return

    for folder in [d for d in root.iterdir() if d.is_dir() and any(d.glob("Season *"))]:
        dest = DEST_LIBRARY / folder.name
        print(f"MOVE: {folder.name}")
        try:
            if dest.exists():
                for item in folder.iterdir():
                    if (
                        item.is_dir()
                        and item.name.startswith("Season")
                        and (dest / item.name).is_dir()
                    ):
                        for media in item.iterdir():
                            move_path(media, dest / item.name / media.name)
                        item.rmdir()
                    else:
                        move_path(item, dest / item.name)
                shutil.rmtree(folder)
            else:
                shutil.move(str(folder), str(dest))
        except Exception as e:
            print(f"Ошибка переноса: {e}")


def action_rename(root: Path) -> None:
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        for s_dir in folder.glob("Season *"):
            if not s_dir.is_dir():
                continue

            s_num = int(s_dir.name.split()[-1])
            files = sorted([f for f in s_dir.iterdir() if f.suffix.lower() == ".mkv"])
            pending = []
            for i, f in enumerate(files, 1):
                target = s_dir / f"{folder.name} - S{s_num:02d}E{i:02d}.mkv"
                if f == target:
                    continue
                pending.append((f, target))

            temp_moves = []
            for f, target in pending:
                temp = unique_path(s_dir / f".rename-tmp-{f.name}")
                f.rename(temp)
                temp_moves.append((temp, target))

            for temp, target in temp_moves:
                temp.rename(unique_path(target))
    print("Готово.")


def action_merge(root: Path) -> None:
    mode = input("Исходники: [m]ove / [k]eep / [d]elete [m]: ").lower() or "m"
    jobs = int(input("Потоков [2]: ") or "2")
    keep_mode = {"k": "keep", "d": "delete", "m": "move"}.get(mode, "move")
    plans = build_plans(root)
    tasks = []

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for plan in plans:
            tasks.append(pool.submit(process_plan, plan, keep_mode))
        for i, fut in enumerate(as_completed(tasks), 1):
            print(f"[{i}/{len(tasks)}] {fut.result()}")


def main_menu(root: Path) -> None:
    while True:
        print_welcome()
        print(f"Рабочая директория: {root}")
        print(
            "1) MERGE: Собрать серии\n"
            "2) RENAME: Jellyfin SxxExx\n"
            "3) CLEANUP: Удалить пустые папки\n"
            "4) DRY RUN: План работ\n"
            "5) FINAL CONSOLIDATE: Склеить сезоны\n"
            "6) MOVE TO LIBRARY: Перенести в /data/anime\n"
            "7) DELETE EXTERNAL SUBS: удалить .ass/.srt/.ssa\n"
            "8) EXIT: Выход"
        )
        choice = input(">> ")
        if choice == "1":
            action_merge(root)
        elif choice == "2":
            action_rename(root)
        elif choice == "3":
            for d in sorted(root.rglob("*"), key=lambda x: len(str(x)), reverse=True):
                if d.is_dir() and not any(d.iterdir()) and d != root:
                    d.rmdir()
            print("Очищено.")
        elif choice == "4":
            action_dry_run(root)
        elif choice == "5":
            action_final_consolidate(root)
        elif choice == "6":
            action_move_to_library(root)
        elif choice == "7":
            action_delete_external_subtitles(root)
        elif choice == "8":
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    main_menu(Path(args.root).resolve())
