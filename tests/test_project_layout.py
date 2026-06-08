from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ProjectLayoutTest(unittest.TestCase):
    def test_source_document_exists(self):
        source_document = PROJECT_ROOT / "source" / "走遍美国中英文对照.docx"

        self.assertTrue(source_document.is_file())

    def test_claude_documents_generated_file_rules(self):
        project_rules = (PROJECT_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        self.assertIn(
            "Do not manually edit generated site files in the `docs/` root",
            project_rules,
        )
        self.assertIn(
            "Files under `docs/superpowers/` are authored project documentation",
            project_rules,
        )


if __name__ == "__main__":
    unittest.main()
