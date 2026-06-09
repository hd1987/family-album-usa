from pathlib import Path
import tempfile
import unittest

from scripts.build_site import build_site, validate_site


ROOT = Path(__file__).resolve().parents[1]


class BuildSiteTest(unittest.TestCase):
    def test_build_writes_complete_github_pages_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)

            build_site(ROOT / "data" / "episodes.json", output_dir)

            self.assertTrue((output_dir / "index.html").is_file())
            self.assertEqual(
                len(list(output_dir.glob("episode-*.html"))),
                26,
            )
            self.assertEqual(
                (output_dir / "CNAME").read_text(encoding="utf-8"),
                "usa.adihuang.com\n",
            )
            self.assertTrue((output_dir / ".nojekyll").is_file())
            validate_site(output_dir)

    def test_build_preserves_authored_superpowers_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            authored = output_dir / "superpowers" / "specs" / "keep.md"
            authored.parent.mkdir(parents=True)
            authored.write_text("keep\n", encoding="utf-8")

            build_site(ROOT / "data" / "episodes.json", output_dir)

            self.assertEqual(authored.read_text(encoding="utf-8"), "keep\n")

    def test_validation_rejects_broken_local_link(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            build_site(ROOT / "data" / "episodes.json", output_dir)
            index = output_dir / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "episode-01.html",
                    "missing.html",
                    1,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Broken local target"):
                validate_site(output_dir)


if __name__ == "__main__":
    unittest.main()
