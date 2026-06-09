from pathlib import Path
import json
import tempfile
import unittest

from scripts.build_content import build_content, validate_episodes


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "走遍美国中英文对照.docx"


class BuildContentTest(unittest.TestCase):
    def test_full_source_builds_26_episodes_with_three_acts(self):
        episodes, issues = build_content(SOURCE)

        validate_episodes(episodes, issues)
        self.assertEqual(
            [episode.number for episode in episodes],
            list(range(1, 27)),
        )
        self.assertTrue(
            all(
                [act.number for act in episode.acts] == [1, 2, 3]
                for episode in episodes
            )
        )

    def test_writer_creates_auditable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)

            build_content(SOURCE, output_dir=output_dir)

            episodes = json.loads(
                (output_dir / "episodes.json").read_text(encoding="utf-8")
            )
            report = json.loads(
                (output_dir / "cleanup-report.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(len(episodes), 26)
        self.assertIn("corrections", report)
        self.assertIn("unresolved", report)
        self.assertTrue(
            any(
                item["category"] == "inserted-act-boundary"
                for item in report["unresolved"]
            )
        )

    def test_validation_rejects_dialogue_without_english(self):
        episodes, issues = build_content(SOURCE)
        episodes[0].acts[0].lines[0].english = ""

        with self.assertRaisesRegex(ValueError, "speaker or English"):
            validate_episodes(episodes, issues)


if __name__ == "__main__":
    unittest.main()
