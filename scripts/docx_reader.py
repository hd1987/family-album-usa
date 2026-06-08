from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{WORD_NAMESPACE}}}"


@dataclass(frozen=True)
class Run:
    text: str
    color: str | None


@dataclass(frozen=True)
class Paragraph:
    number: int
    text: str
    runs: list[Run]


def read_docx(path: Path) -> list[Paragraph]:
    with ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")

    root = ElementTree.fromstring(document_xml)
    body = root.find(f"{W}body")
    if body is None:
        return []

    paragraphs = []
    for number, paragraph_element in enumerate(body.findall(f"{W}p"), start=1):
        runs = [
            _read_run(run_element)
            for run_element in paragraph_element.findall(f"{W}r")
        ]
        text = "".join(run.text for run in runs)
        if text.strip():
            paragraphs.append(Paragraph(number=number, text=text, runs=runs))

    return paragraphs


def _read_run(run_element: ElementTree.Element) -> Run:
    text = "".join(
        text_element.text or "" for text_element in run_element.findall(f"{W}t")
    )
    color_element = run_element.find(f"{W}rPr/{W}color")
    color = color_element.get(f"{W}val") if color_element is not None else None
    return Run(text=text, color=color)
