from pathlib import Path
import unittest

from scripts.docx_reader import read_docx


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.docx"


class DocxReaderTest(unittest.TestCase):
    def test_reads_nonempty_paragraphs_with_source_numbers(self):
        paragraphs = read_docx(FIXTURE_PATH)

        self.assertEqual([paragraph.number for paragraph in paragraphs], [1, 3, 4])

    def test_reads_first_paragraph_text(self):
        paragraphs = read_docx(FIXTURE_PATH)

        self.assertEqual(paragraphs[0].text, "Episode 1 - A Family Album")

    def test_reads_speaker_run_text_and_color(self):
        paragraphs = read_docx(FIXTURE_PATH)

        self.assertEqual(paragraphs[1].runs[0].text, "Richard：")
        self.assertEqual(paragraphs[1].runs[0].color, "FF0000")


if __name__ == "__main__":
    unittest.main()
