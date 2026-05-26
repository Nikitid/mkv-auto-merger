import importlib.util
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mkv-auto-merge.py"


def load_script():
    spec = importlib.util.spec_from_file_location("mkv_auto_merge_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load mkv-auto-merge.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MkvAutoMergeScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_script()

    def test_episode_data_finds_dts_audio(self) -> None:
        with TemporaryDirectory() as tmp:
            title_dir = Path(tmp) / "Show S01"
            sounds_dir = title_dir / "Sounds" / "Studio"
            sounds_dir.mkdir(parents=True)
            video = title_dir / "Show - 01.mkv"
            audio = sounds_dir / "Show - 01.dts"
            video.touch()
            audio.touch()

            audios, subs = self.script.get_episode_data(title_dir, video)

            self.assertEqual([("Studio", audio)], audios)
            self.assertEqual([], subs)

    def test_build_plan_ignores_subtitles_and_strips_embedded_subs(self) -> None:
        with TemporaryDirectory() as tmp:
            title_dir = Path(tmp) / "Show S01"
            sounds_dir = title_dir / "DUB" / "AniLibria"
            sounds_dir.mkdir(parents=True)
            video = title_dir / "[Tracker] Show S01E02 1080p.mkv"
            audio = sounds_dir / "Show - 02.flac"
            sub = title_dir / "Show - 02.ass"
            video.touch()
            audio.touch()
            sub.touch()

            plan = self.script.build_episode_plan(
                title_dir,
                self.script.MediaRef(video, season=1, episode=2),
            )
            cmd = self.script.build_mkvmerge_command(plan)

            self.assertEqual([("AniLibria", audio)], list(plan.audios))
            self.assertEqual((sub,), plan.ignored_subtitles)
            self.assertIn("--no-subtitles", cmd)
            self.assertNotIn(str(sub), cmd)
            self.assertEqual(title_dir.parent / "Show" / "Season 01", plan.output_file.parent)
            self.assertEqual("Show - S01E02.mkv", plan.output_file.name)

    def test_bonus_video_goes_to_season_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            title_dir = Path(tmp) / "Show S02"
            bonus_dir = title_dir / "Bonus"
            bonus_dir.mkdir(parents=True)
            video = bonus_dir / "OVA 01.mkv"
            video.touch()

            plans = self.script.build_plans(Path(tmp))

            self.assertEqual(1, len(plans))
            self.assertTrue(plans[0].video.is_bonus)
            self.assertEqual(0, plans[0].video.season)
            self.assertEqual("Show - S00E01.mkv", plans[0].output_file.name)

    def test_source_season_folder_is_processed_but_existing_output_is_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            title_dir = Path(tmp) / "Show"
            source_season = title_dir / "Season 1"
            source_season.mkdir(parents=True)
            (source_season / "01.mkv").touch()

            plans = self.script.build_plans(Path(tmp))

            self.assertEqual(1, len(plans))
            self.assertEqual(title_dir / "Season 01" / "Show - S01E01.mkv", plans[0].output_file)

            plans[0].output_file.parent.mkdir(parents=True)
            plans[0].output_file.touch()

            plans_after_output = self.script.build_plans(Path(tmp))

            self.assertEqual(1, len(plans_after_output))
            self.assertEqual(source_season / "01.mkv", plans_after_output[0].video.path)

    def test_unique_path_keeps_existing_files(self) -> None:
        with TemporaryDirectory() as tmp:
            existing = Path(tmp) / "episode.mkv"
            existing.touch()

            self.assertEqual(Path(tmp) / "episode (1).mkv", self.script.unique_path(existing))

    def test_move_to_library_merges_seasons_without_overwriting(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "work"
            library = Path(tmp) / "library"
            root.mkdir()

            source_season = root / "Show" / "Season 01"
            dest_season = library / "Show" / "Season 01"
            source_season.mkdir(parents=True)
            dest_season.mkdir(parents=True)
            (source_season / "S01E01.mkv").write_text("new", encoding="utf-8")
            (dest_season / "S01E01.mkv").write_text("old", encoding="utf-8")

            old_dest_library = self.script.DEST_LIBRARY
            self.script.DEST_LIBRARY = library
            try:
                with redirect_stdout(StringIO()):
                    self.script.action_move_to_library(root)
            finally:
                self.script.DEST_LIBRARY = old_dest_library

            self.assertEqual("old", (dest_season / "S01E01.mkv").read_text(encoding="utf-8"))
            self.assertEqual("new", (dest_season / "S01E01 (1).mkv").read_text(encoding="utf-8"))
            self.assertFalse((root / "Show").exists())
