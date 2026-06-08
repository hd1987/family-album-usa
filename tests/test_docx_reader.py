from pathlib import Path
import unittest
from zipfile import ZipFile

from scripts.docx_reader import Run, read_paragraphs


FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"
DOCX_FIXTURE_PATH = FIXTURE_DIRECTORY / "sample.docx"
XML_FIXTURE_PATH = FIXTURE_DIRECTORY / "sample-document.xml"


class DocxReaderTest(unittest.TestCase):
    def test_reads_nonempty_paragraphs_with_source_numbers(self):
        paragraphs = read_paragraphs(DOCX_FIXTURE_PATH)

        self.assertEqual([paragraph.number for paragraph in paragraphs], [1, 3, 4])

    def test_strips_paragraph_text(self):
        paragraphs = read_paragraphs(DOCX_FIXTURE_PATH)

        self.assertEqual(paragraphs[0].text, "Episode 1 - A Family Album")
        self.assertEqual(paragraphs[2].text, "Act 1")

    def test_reads_complete_speaker_text(self):
        paragraphs = read_paragraphs(DOCX_FIXTURE_PATH)

        self.assertEqual(paragraphs[1].text, "Richard： Excuse me.对不起。")

    def test_reads_nonempty_runs_with_color_metadata(self):
        paragraphs = read_paragraphs(DOCX_FIXTURE_PATH)

        self.assertEqual(
            [paragraph.runs for paragraph in paragraphs],
            [
                [Run(text="  Episode 1 - A Family Album  ", color=None)],
                [
                    Run(text="Richard：", color="FF0000"),
                    Run(text=" Excuse me.", color=None),
                    Run(text="对不起。", color=None),
                ],
                [Run(text=" Act 1 ", color=None)],
            ],
        )

    def test_docx_contains_xml_fixture(self):
        with ZipFile(DOCX_FIXTURE_PATH) as archive:
            document_xml = archive.read("word/document.xml")

        self.assertEqual(document_xml, XML_FIXTURE_PATH.read_bytes())


if __name__ == "__main__":
    unittest.main()
