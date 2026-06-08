# Static Bilingual Reader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the source DOCX into a validated, responsive, bilingual static reading site ready for GitHub Pages at `usa.adihuang.com`.

**Architecture:** A Python standard-library build pipeline extracts WordprocessingML, normalizes it into typed episode data, records deterministic corrections, and renders static HTML through small focused modules. Generated HTML contains the full bilingual text; CSS controls the responsive two-column layout and progressive-enhancement JavaScript only persists Chinese visibility.

**Tech Stack:** Python 3 standard library, `unittest`, HTML5, CSS, vanilla JavaScript, GitHub Pages.

---

## File Map

- `source/走遍美国中英文对照.docx`: immutable source document.
- `scripts/models.py`: normalized content dataclasses and JSON serialization.
- `scripts/docx_reader.py`: low-level DOCX paragraph and run extraction.
- `scripts/normalize.py`: episode, act, speaker, language, and correction logic.
- `scripts/build_content.py`: content build orchestration and validation.
- `scripts/render.py`: HTML escaping and page rendering.
- `scripts/build_site.py`: static-site orchestration and asset copying.
- `templates/index.html`: directory page template.
- `templates/episode.html`: episode page template.
- `assets/styles.css`: paper-script visual system and responsive layout.
- `assets/reader.js`: Chinese visibility preference only.
- `data/episodes.json`: generated normalized content.
- `data/cleanup-report.json`: generated corrections and unresolved issues.
- `docs/`: generated GitHub Pages site.
- `tests/fixtures/`: small deterministic DOCX/XML and normalized-data fixtures.
- `tests/test_models.py`: content model tests.
- `tests/test_docx_reader.py`: DOCX extraction tests.
- `tests/test_normalize.py`: structural cleanup and correction tests.
- `tests/test_build_content.py`: full source-content invariants.
- `tests/test_render.py`: HTML rendering tests.
- `tests/test_build_site.py`: generated-site and link tests.
- `tests/test_reader_js.mjs`: browser-independent JavaScript behavior tests.

## Task 1: Establish Source Layout And Test Command

**Files:**
- Create: `source/走遍美国中英文对照.docx`
- Create: `tests/__init__.py`
- Create: `tests/test_project_layout.py`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write the failing project-layout test**

```python
# tests/test_project_layout.py
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectLayoutTest(unittest.TestCase):
    def test_source_document_is_stored_in_source_directory(self):
        source = ROOT / "source" / "走遍美国中英文对照.docx"
        self.assertTrue(source.is_file())

    def test_generated_directories_are_not_hand_maintained_inputs(self):
        rules = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("Do not manually edit generated site files", rules)
        self.assertIn("Files under `docs/superpowers/` are authored", rules)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify the missing source path**

Run:

```bash
python3 -m unittest tests.test_project_layout -v
```

Expected: `test_source_document_is_stored_in_source_directory` fails because
`source/走遍美国中英文对照.docx` does not exist.

- [ ] **Step 3: Stop for protected-operation approval**

Ask the user for explicit approval to move:

```text
走遍美国中英文对照.docx
```

to:

```text
source/走遍美国中英文对照.docx
```

Do not continue this task until approval is received because relocation removes
the file from its current path.

- [ ] **Step 4: Create the source directory and move the approved file**

Run:

```bash
mkdir -p source tests
mv "走遍美国中英文对照.docx" "source/走遍美国中英文对照.docx"
touch tests/__init__.py
```

Expected: the DOCX exists only under `source/`.

- [ ] **Step 5: Clarify generated-file validation in the project rules**

Confirm this exact rule remains beneath `## Source And Generated Files`:

```markdown
Files under `docs/superpowers/` are authored project documentation and must
never be removed by site generation.
```

- [ ] **Step 6: Run the test**

Run:

```bash
python3 -m unittest tests.test_project_layout -v
```

Expected: 2 tests pass.

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md source/ tests/
git commit -m "Organize the source document."
```

## Task 2: Define The Normalized Content Model

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing model serialization tests**

```python
# tests/test_models.py
import unittest

from scripts.models import Act, Correction, DialogueLine, Episode


class ContentModelTest(unittest.TestCase):
    def test_episode_serializes_with_traceable_dialogue(self):
        episode = Episode(
            number=1,
            english_title="46 Linden Street",
            chinese_title="林登大街 46 号",
            acts=[
                Act(
                    number=1,
                    lines=[
                        DialogueLine(
                            speaker="Richard",
                            english="Excuse me.",
                            chinese="对不起。",
                            source_paragraphs=[38],
                            corrections=[
                                Correction(
                                    category="spacing",
                                    before="Excuse  me.",
                                    after="Excuse me.",
                                    confidence="certain",
                                )
                            ],
                        )
                    ],
                )
            ],
        )

        payload = episode.to_dict()

        self.assertEqual(payload["number"], 1)
        self.assertEqual(payload["acts"][0]["lines"][0]["speaker"], "Richard")
        self.assertEqual(
            payload["acts"][0]["lines"][0]["source_paragraphs"], [38]
        )
        self.assertEqual(
            payload["acts"][0]["lines"][0]["corrections"][0]["category"],
            "spacing",
        )

    def test_model_rejects_invalid_act_number(self):
        with self.assertRaisesRegex(ValueError, "act number"):
            Act(number=0, lines=[])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify import failure**

Run:

```bash
python3 -m unittest tests.test_models -v
```

Expected: FAIL with `ModuleNotFoundError` for `scripts.models`.

- [ ] **Step 3: Implement focused dataclasses**

```python
# scripts/models.py
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Correction:
    category: str
    before: str
    after: str
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DialogueLine:
    speaker: str
    english: str
    chinese: str
    source_paragraphs: list[int]
    corrections: list[Correction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaker": self.speaker,
            "english": self.english,
            "chinese": self.chinese,
            "source_paragraphs": self.source_paragraphs,
            "corrections": [item.to_dict() for item in self.corrections],
        }


@dataclass
class Act:
    number: int
    lines: list[DialogueLine]

    def __post_init__(self) -> None:
        if self.number not in {1, 2, 3}:
            raise ValueError(f"Invalid act number: {self.number}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "lines": [line.to_dict() for line in self.lines],
        }


@dataclass
class Episode:
    number: int
    english_title: str
    chinese_title: str
    acts: list[Act]

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "english_title": self.english_title,
            "chinese_title": self.chinese_title,
            "acts": [act.to_dict() for act in self.acts],
        }
```

Create empty package markers:

```python
# scripts/__init__.py
```

- [ ] **Step 4: Run the model tests**

Run:

```bash
python3 -m unittest tests.test_models -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/ tests/test_models.py
git commit -m "Define the bilingual content model."
```

## Task 3: Extract Paragraphs And Run Metadata From DOCX

**Files:**
- Create: `scripts/docx_reader.py`
- Create: `tests/fixtures/sample-document.xml`
- Create: `tests/fixtures/sample.docx`
- Create: `tests/test_docx_reader.py`

- [ ] **Step 1: Add the extraction tests**

```python
# tests/test_docx_reader.py
from pathlib import Path
import unittest

from scripts.docx_reader import read_paragraphs


FIXTURES = Path(__file__).parent / "fixtures"


class DocxReaderTest(unittest.TestCase):
    def test_extracts_text_runs_colors_and_source_numbers(self):
        paragraphs = read_paragraphs(FIXTURES / "sample.docx")

        self.assertEqual(paragraphs[0].number, 1)
        self.assertEqual(paragraphs[0].text, "EPISODE 1 46 Linden Street")
        self.assertEqual(paragraphs[2].runs[0].text, "Richard：")
        self.assertEqual(paragraphs[2].runs[0].color, "FF0000")

    def test_skips_empty_paragraphs_without_renumbering_source(self):
        paragraphs = read_paragraphs(FIXTURES / "sample.docx")

        self.assertEqual([item.number for item in paragraphs], [1, 3, 4])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Create the minimal XML fixture**

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>EPISODE 1 46 Linden Street</w:t></w:r></w:p>
    <w:p/>
    <w:p>
      <w:r><w:rPr><w:color w:val="FF0000"/></w:rPr><w:t>Richard：</w:t></w:r>
      <w:r><w:t> Excuse me.</w:t></w:r>
      <w:r><w:t>对不起。</w:t></w:r>
    </w:p>
    <w:p><w:r><w:t>Act 1.</w:t></w:r></w:p>
  </w:body>
</w:document>
```

Create `sample.docx` with a short test helper command:

```bash
mkdir -p tests/fixtures/.docx/word
cp tests/fixtures/sample-document.xml tests/fixtures/.docx/word/document.xml
cd tests/fixtures/.docx
zip -qr ../sample.docx word
cd ../../..
```

- [ ] **Step 3: Run the test and verify import failure**

Run:

```bash
python3 -m unittest tests.test_docx_reader -v
```

Expected: FAIL because `scripts.docx_reader` does not exist.

- [ ] **Step 4: Implement the standard-library DOCX reader**

```python
# scripts/docx_reader.py
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}


@dataclass(frozen=True)
class Run:
    text: str
    color: str | None


@dataclass(frozen=True)
class Paragraph:
    number: int
    text: str
    runs: list[Run]


def _attribute(name: str) -> str:
    return f"{{{WORD_NS}}}{name}"


def read_paragraphs(path: Path) -> list[Paragraph]:
    with ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))

    paragraphs: list[Paragraph] = []
    for number, node in enumerate(root.findall(".//w:body/w:p", NS), start=1):
        runs: list[Run] = []
        for run_node in node.findall("w:r", NS):
            text = "".join(
                text_node.text or ""
                for text_node in run_node.findall(".//w:t", NS)
            )
            if not text:
                continue
            color_node = run_node.find("w:rPr/w:color", NS)
            color = (
                color_node.get(_attribute("val"))
                if color_node is not None
                else None
            )
            runs.append(Run(text=text, color=color))
        text = "".join(run.text for run in runs).strip()
        if text:
            paragraphs.append(Paragraph(number=number, text=text, runs=runs))
    return paragraphs
```

- [ ] **Step 5: Run the extraction tests**

Run:

```bash
python3 -m unittest tests.test_docx_reader -v
```

Expected: 2 tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/docx_reader.py tests/fixtures tests/test_docx_reader.py
git commit -m "Extract structured text from the source document."
```

## Task 4: Normalize Episodes, Acts, Dialogue, And Corrections

**Files:**
- Create: `scripts/normalize.py`
- Create: `tests/test_normalize.py`

- [ ] **Step 1: Write failing normalization tests**

```python
# tests/test_normalize.py
import unittest

from scripts.docx_reader import Paragraph, Run
from scripts.normalize import normalize_document


def paragraph(number: int, text: str, color: str | None = None) -> Paragraph:
    return Paragraph(number=number, text=text, runs=[Run(text=text, color=color)])


class NormalizeDocumentTest(unittest.TestCase):
    def test_discards_front_matter_and_builds_dialogue(self):
        source = [
            paragraph(1, "EPISODE 1 46 Linden Street林登大街 46 号"),
            paragraph(2, "Richard：", "FF0000"),
            paragraph(3, "EPISODE 1 46 Linden Street林登大街 46 号"),
            paragraph(4, "Act1."),
            paragraph(
                5,
                "Alexadra： Excue me.对不起。",
                "FF0000",
            ),
            paragraph(6, "Act 2."),
            paragraph(7, "Richard： What's it for?做什么用？"),
            paragraph(8, "Act 3."),
            paragraph(9, "Richard： Thank you.谢谢。"),
        ]

        episodes, issues = normalize_document(source)

        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].english_title, "46 Linden Street")
        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.speaker, "Alexandra")
        self.assertEqual(line.english, "Excuse me.")
        self.assertEqual(line.chinese, "对不起。")
        self.assertEqual(len(line.corrections), 2)
        self.assertEqual(issues, [])

    def test_merges_continuation_paragraphs_into_previous_dialogue(self):
        source = [
            paragraph(1, "EPISODE 1 46 Linden Street"),
            paragraph(2, "Act 1."),
            paragraph(3, "Harry： Can I speak"),
            paragraph(4, "to Betty?我能跟 Betty 说话吗？"),
            paragraph(5, "Act 2."),
            paragraph(6, "Harry： Thanks.谢谢。"),
            paragraph(7, "Act 3."),
            paragraph(8, "Harry： Bye.再见。"),
        ]

        episodes, _ = normalize_document(source)

        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.english, "Can I speak to Betty?")
        self.assertEqual(line.chinese, "我能跟 Betty 说话吗？")
        self.assertEqual(line.source_paragraphs, [3, 4])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify import failure**

Run:

```bash
python3 -m unittest tests.test_normalize -v
```

Expected: FAIL because `scripts.normalize` does not exist.

- [ ] **Step 3: Implement normalization with explicit correction tables**

Create `scripts/normalize.py`:

```python
from dataclasses import dataclass
import re

from scripts.docx_reader import Paragraph
from scripts.models import Act, Correction, DialogueLine, Episode


@dataclass(frozen=True)
class CleanupIssue:
    episode: int | None
    act: int | None
    source_paragraphs: list[int]
    category: str
    source_text: str
    detail: str
    confidence: str

    def to_dict(self) -> dict[str, object]:
        return {
            "episode": self.episode,
            "act": self.act,
            "source_paragraphs": self.source_paragraphs,
            "category": self.category,
            "source_text": self.source_text,
            "detail": self.detail,
            "confidence": self.confidence,
        }


SPEAKER_CORRECTIONS = {
    "Alexadra": "Alexandra",
    "Alexanra": "Alexandra",
    "Marllyn": "Marilyn",
}

TEXT_CORRECTIONS = {
    "Excue me.": "Excuse me.",
    "northem Greece": "northern Greece",
}

EPISODE_PATTERN = re.compile(r"^episode\s+(\d+)\s*(.*)$", re.IGNORECASE)
ACT_PATTERN = re.compile(r"^act\s*([123])\s*\.?$", re.IGNORECASE)
SPEAKER_PATTERN = re.compile(r"^([^：;]{1,32})[：;]\s*(.*)$")
CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")
SPACE_PATTERN = re.compile(r"\s+")
SUSPECT_PATTERNS = (re.compile(r"\byuo\b", re.IGNORECASE),)


def _content_start(paragraphs: list[Paragraph]) -> int:
    candidates = [
        index
        for index, paragraph in enumerate(paragraphs)
        if re.match(r"^episode\s+1(?:\D|$)", paragraph.text, re.IGNORECASE)
    ]
    if not candidates:
        raise ValueError("Episode 1 heading not found")
    return candidates[-1]


def _split_title(text: str) -> tuple[int, str, str]:
    match = EPISODE_PATTERN.match(text.strip())
    if match is None:
        raise ValueError(f"Invalid episode heading: {text}")
    number = int(match.group(1))
    title = match.group(2).strip()
    cjk = CJK_PATTERN.search(title)
    if cjk is None:
        return number, title, ""
    return number, title[: cjk.start()].strip(), title[cjk.start() :].strip()


def _split_languages(text: str) -> tuple[str, str]:
    cjk = CJK_PATTERN.search(text)
    if cjk is None:
        return text.strip(), ""
    return text[: cjk.start()].strip(), text[cjk.start() :].strip()


def _normalize_speaker(name: str) -> tuple[str, list[Correction]]:
    before = SPACE_PATTERN.sub(" ", name).strip()
    after = SPEAKER_CORRECTIONS.get(before, before)
    corrections = []
    if after != before:
        corrections.append(
            Correction(
                category="speaker",
                before=before,
                after=after,
                confidence="certain",
            )
        )
    return after, corrections


def _normalize_text(text: str) -> tuple[str, list[Correction]]:
    value = SPACE_PATTERN.sub(" ", text).strip()
    corrections = []
    for before, after in TEXT_CORRECTIONS.items():
        if before in value:
            updated = value.replace(before, after)
            corrections.append(
                Correction(
                    category="spelling",
                    before=value,
                    after=updated,
                    confidence="certain",
                )
            )
            value = updated
    return value, corrections


def _join_text(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    return f"{left.rstrip()} {right.lstrip()}".strip()


def _append_continuation(
    line: DialogueLine,
    paragraph: Paragraph,
) -> None:
    english, chinese = _split_languages(paragraph.text)
    normalized_english, corrections = _normalize_text(english)
    line.english = _join_text(line.english, normalized_english)
    line.chinese = _join_text(line.chinese, chinese)
    line.source_paragraphs.append(paragraph.number)
    line.corrections.extend(corrections)


def _record_suspect_text(
    issues: list[CleanupIssue],
    episode: int,
    act: int,
    paragraph: Paragraph,
) -> None:
    if any(pattern.search(paragraph.text) for pattern in SUSPECT_PATTERNS):
        issues.append(
            CleanupIssue(
                episode=episode,
                act=act,
                source_paragraphs=[paragraph.number],
                category="suspected-typo",
                source_text=paragraph.text,
                detail="Preserved because the intended correction is uncertain",
                confidence="uncertain",
            )
        )


def normalize_document(
    paragraphs: list[Paragraph],
) -> tuple[list[Episode], list[CleanupIssue]]:
    episodes: list[Episode] = []
    issues: list[CleanupIssue] = []
    current_episode: Episode | None = None
    current_act: Act | None = None
    current_line: DialogueLine | None = None

    for paragraph in paragraphs[_content_start(paragraphs) :]:
        if EPISODE_PATTERN.match(paragraph.text):
            number, english_title, chinese_title = _split_title(paragraph.text)
            current_episode = Episode(
                number=number,
                english_title=english_title,
                chinese_title=chinese_title,
                acts=[],
            )
            episodes.append(current_episode)
            current_act = None
            current_line = None
            continue

        act_match = ACT_PATTERN.match(paragraph.text)
        if act_match:
            if current_episode is None:
                raise ValueError("Act heading appears before an episode")
            current_act = Act(number=int(act_match.group(1)), lines=[])
            current_episode.acts.append(current_act)
            current_line = None
            continue

        if current_episode is None or current_act is None:
            issues.append(
                CleanupIssue(
                    episode=current_episode.number if current_episode else None,
                    act=current_act.number if current_act else None,
                    source_paragraphs=[paragraph.number],
                    category="orphan-paragraph",
                    source_text=paragraph.text,
                    detail="Paragraph appears outside an episode act",
                    confidence="certain",
                )
            )
            continue

        speaker_match = SPEAKER_PATTERN.match(paragraph.text)
        if speaker_match:
            speaker, speaker_corrections = _normalize_speaker(
                speaker_match.group(1)
            )
            english, chinese = _split_languages(speaker_match.group(2))
            english, text_corrections = _normalize_text(english)
            current_line = DialogueLine(
                speaker=speaker,
                english=english,
                chinese=chinese,
                source_paragraphs=[paragraph.number],
                corrections=speaker_corrections + text_corrections,
            )
            current_act.lines.append(current_line)
            _record_suspect_text(
                issues,
                current_episode.number,
                current_act.number,
                paragraph,
            )
            continue

        if current_line is None:
            issues.append(
                CleanupIssue(
                    episode=current_episode.number,
                    act=current_act.number,
                    source_paragraphs=[paragraph.number],
                    category="unassigned-continuation",
                    source_text=paragraph.text,
                    detail="No preceding dialogue accepts this continuation",
                    confidence="uncertain",
                )
            )
            continue

        _append_continuation(current_line, paragraph)
        _record_suspect_text(
            issues,
            current_episode.number,
            current_act.number,
            paragraph,
        )

    for episode in episodes:
        for act in episode.acts:
            for line in act.lines:
                if not line.chinese:
                    issues.append(
                        CleanupIssue(
                            episode=episode.number,
                            act=act.number,
                            source_paragraphs=line.source_paragraphs,
                            category="missing-chinese",
                            source_text=line.english,
                            detail="No Chinese translation was found",
                            confidence="certain",
                        )
                    )

    return episodes, issues
```

- [ ] **Step 4: Run normalization tests**

Run:

```bash
python3 -m unittest tests.test_normalize -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Add regression cases from the real document**

Add table-driven tests for:

```python
cases = {
    "Alexadra": "Alexandra",
    "Alexanra": "Alexandra",
    "Marllyn": "Marilyn",
    "Act1.": 1,
    "Act2.": 2,
    "Act3.": 3,
}
```

Also add a test proving uncertain text such as `yuo from in Florida?` is
preserved and reported instead of silently corrected.

- [ ] **Step 6: Run normalization tests again**

Run:

```bash
python3 -m unittest tests.test_normalize -v
```

Expected: all normalization tests pass.

- [ ] **Step 7: Commit**

```bash
git add scripts/normalize.py tests/test_normalize.py
git commit -m "Normalize bilingual episode content."
```

## Task 5: Build And Validate The Full Content Dataset

**Files:**
- Create: `scripts/build_content.py`
- Create: `tests/test_build_content.py`
- Generate: `data/episodes.json`
- Generate: `data/cleanup-report.json`

- [ ] **Step 1: Write failing build validation tests**

```python
# tests/test_build_content.py
from pathlib import Path
import json
import unittest

from scripts.build_content import build_content, validate_episodes


ROOT = Path(__file__).resolve().parents[1]


class BuildContentTest(unittest.TestCase):
    def test_full_source_builds_26_episodes_with_three_acts(self):
        episodes, issues = build_content(
            ROOT / "source" / "走遍美国中英文对照.docx"
        )

        validate_episodes(episodes, issues)
        self.assertEqual([episode.number for episode in episodes], list(range(1, 27)))
        self.assertTrue(all(len(episode.acts) == 3 for episode in episodes))

    def test_writer_creates_auditable_json(self):
        build_content(
            ROOT / "source" / "走遍美国中英文对照.docx",
            output_dir=ROOT / "data",
        )

        episodes = json.loads(
            (ROOT / "data" / "episodes.json").read_text(encoding="utf-8")
        )
        report = json.loads(
            (ROOT / "data" / "cleanup-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(episodes), 26)
        self.assertIn("corrections", report)
        self.assertIn("unresolved", report)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and capture real-source failures**

Run:

```bash
python3 -m unittest tests.test_build_content -v
```

Expected: FAIL because `scripts.build_content` does not exist.

- [ ] **Step 3: Implement build orchestration and strict validation**

```python
# scripts/build_content.py
from argparse import ArgumentParser
from pathlib import Path
import json

from scripts.docx_reader import read_paragraphs
from scripts.models import Episode
from scripts.normalize import CleanupIssue, normalize_document


def validate_episodes(
    episodes: list[Episode],
    issues: list[CleanupIssue],
) -> None:
    if [episode.number for episode in episodes] != list(range(1, 27)):
        raise ValueError("Expected sequential episodes 1 through 26")
    for episode in episodes:
        if [act.number for act in episode.acts] != [1, 2, 3]:
            raise ValueError(f"Episode {episode.number} must contain acts 1, 2, 3")
        for act in episode.acts:
            for line in act.lines:
                if not line.speaker or not line.english:
                    raise ValueError(
                        f"Episode {episode.number} act {act.number} "
                        "contains dialogue without speaker or English text"
                    )


def build_content(
    source: Path,
    output_dir: Path | None = None,
) -> tuple[list[Episode], list[CleanupIssue]]:
    episodes, issues = normalize_document(read_paragraphs(source))
    validate_episodes(episodes, issues)
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "episodes.json").write_text(
            json.dumps(
                [episode.to_dict() for episode in episodes],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        corrections = [
            {
                "episode": episode.number,
                "act": act.number,
                "speaker": line.speaker,
                "source_paragraphs": line.source_paragraphs,
                "correction": correction.to_dict(),
            }
            for episode in episodes
            for act in episode.acts
            for line in act.lines
            for correction in line.corrections
        ]
        unresolved = [issue.to_dict() for issue in issues]
        (output_dir / "cleanup-report.json").write_text(
            json.dumps(
                {"corrections": corrections, "unresolved": unresolved},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return episodes, issues


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_content(args.source, args.output_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the full-source tests and resolve only deterministic issues**

Run:

```bash
python3 -m unittest tests.test_build_content -v
```

Expected initially: failures identify missing Act labels, continuation
paragraphs, or malformed speakers in the source.

For each failure:

1. Add the smallest fixture-based regression test to `tests/test_normalize.py`.
2. Update an explicit correction table or structural rule.
3. Preserve uncertain text in the cleanup report.
4. Re-run `tests.test_normalize` before the full-source test.

Do not loosen `validate_episodes` to make malformed content pass.

- [ ] **Step 5: Generate and inspect the content artifacts**

Run:

```bash
python3 -m scripts.build_content \
  "source/走遍美国中英文对照.docx" \
  --output-dir data
python3 -m json.tool data/episodes.json >/dev/null
python3 -m json.tool data/cleanup-report.json >/dev/null
```

Expected: both JSON files parse successfully and the command exits 0.

- [ ] **Step 6: Review unresolved entries**

Run:

```bash
python3 -c 'import json; d=json.load(open("data/cleanup-report.json")); print(len(d["corrections"]), len(d["unresolved"]))'
```

Expected: prints deterministic correction and unresolved counts. Manually
inspect every unresolved entry before committing. Do not change uncertain
dialogue merely to reduce the count.

- [ ] **Step 7: Run all content tests**

Run:

```bash
python3 -m unittest \
  tests.test_models \
  tests.test_docx_reader \
  tests.test_normalize \
  tests.test_build_content \
  -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add scripts/build_content.py scripts/normalize.py tests/ data/
git commit -m "Build the validated episode dataset."
```

## Task 6: Render Directory And Episode HTML

**Files:**
- Create: `scripts/render.py`
- Create: `templates/index.html`
- Create: `templates/episode.html`
- Create: `tests/test_render.py`

- [ ] **Step 1: Write failing renderer tests**

```python
# tests/test_render.py
import unittest

from scripts.models import Act, DialogueLine, Episode
from scripts.render import render_episode_page, render_index_page


EPISODE = Episode(
    number=1,
    english_title="46 Linden Street",
    chinese_title="林登大街 46 号",
    acts=[
        Act(
            number=1,
            lines=[
                DialogueLine(
                    speaker="Richard",
                    english='A <book> & "album".',
                    chinese="一本摄影集。",
                    source_paragraphs=[38],
                )
            ],
        ),
        Act(number=2, lines=[]),
        Act(number=3, lines=[]),
    ],
)


class RenderTest(unittest.TestCase):
    def test_index_contains_episode_link_and_bilingual_title(self):
        html = render_index_page([EPISODE])
        self.assertIn('href="episode-01.html"', html)
        self.assertIn("46 Linden Street", html)
        self.assertIn("林登大街 46 号", html)

    def test_episode_escapes_dialogue_and_renders_act_anchors(self):
        html = render_episode_page(EPISODE, previous=None, following=None)
        self.assertIn('id="act-1"', html)
        self.assertIn("A &lt;book&gt; &amp; &quot;album&quot;.", html)
        self.assertIn('data-chinese-text', html)
        self.assertNotIn('class="previous-episode"', html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify import failure**

Run:

```bash
python3 -m unittest tests.test_render -v
```

Expected: FAIL because `scripts.render` does not exist.

- [ ] **Step 3: Create semantic templates**

`templates/index.html` must include:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="《走遍美国》沉浸式中英文对照剧本">
  <title>走遍美国 · Family Album, U.S.A.</title>
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="index.html">走遍美国</a>
  </header>
  <main class="directory">
    <p class="eyebrow">Family Album, U.S.A.</p>
    <h1>选择一集开始阅读</h1>
    <p class="lede">26 集中英文对照剧本，阅读时可随时隐藏中文。</p>
    {{EPISODE_CARDS}}
  </main>
</body>
</html>
```

`templates/episode.html` must include semantic `<header>`, `<nav>`, `<main>`,
three `<section>` elements, and `<footer>`, plus these replacement tokens:

```text
{{PAGE_TITLE}}
{{EPISODE_NUMBER}}
{{ENGLISH_TITLE}}
{{CHINESE_TITLE}}
{{ACT_LINKS}}
{{ACT_SECTIONS}}
{{PREVIOUS_LINK}}
{{NEXT_LINK}}
```

It must load `assets/styles.css` and load the JavaScript module as:

```html
<script type="module" src="assets/reader.js"></script>
```

- [ ] **Step 4: Implement escaped template rendering**

Create `scripts/render.py` with:

```python
from html import escape
from pathlib import Path

from scripts.models import DialogueLine, Episode


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def _template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def _episode_filename(number: int) -> str:
    return f"episode-{number:02d}.html"


def _render_line(line: DialogueLine) -> str:
    return (
        '<article class="dialogue-line">'
        '<div class="english-column">'
        f'<p class="speaker">{escape(line.speaker)}</p>'
        f'<p class="dialogue-text">{escape(line.english)}</p>'
        "</div>"
        '<div class="chinese-column" data-chinese-text>'
        '<p class="language-label">中文</p>'
        f'<p class="dialogue-text">{escape(line.chinese)}</p>'
        "</div>"
        "</article>"
    )


def render_index_page(episodes: list[Episode]) -> str:
    cards = "".join(
        '<a class="episode-card" '
        f'href="{_episode_filename(episode.number)}">'
        f'<span class="episode-number">{episode.number:02d}</span>'
        f"<strong>{escape(episode.english_title)}</strong>"
        f"<span>{escape(episode.chinese_title)}</span>"
        "</a>"
        for episode in episodes
    )
    return _template("index.html").replace("{{EPISODE_CARDS}}", cards)


def render_episode_page(
    episode: Episode,
    previous: Episode | None,
    following: Episode | None,
) -> str:
    act_links = "".join(
        f'<a href="#act-{act.number}">Act {act.number}</a>'
        for act in episode.acts
    )
    act_sections = "".join(
        '<section class="act" '
        f'id="act-{act.number}" aria-labelledby="act-{act.number}-title">'
        f'<h2 id="act-{act.number}-title">Act {act.number}</h2>'
        f'{"".join(_render_line(line) for line in act.lines)}'
        "</section>"
        for act in episode.acts
    )
    previous_link = (
        '<a class="previous-episode" '
        f'href="{_episode_filename(previous.number)}">'
        f"← Episode {previous.number}: {escape(previous.english_title)}</a>"
        if previous
        else ""
    )
    next_link = (
        '<a class="next-episode" '
        f'href="{_episode_filename(following.number)}">'
        f"Episode {following.number}: {escape(following.english_title)} →</a>"
        if following
        else ""
    )
    replacements = {
        "{{PAGE_TITLE}}": (
            f"Episode {episode.number}: {escape(episode.english_title)}"
        ),
        "{{EPISODE_NUMBER}}": str(episode.number),
        "{{ENGLISH_TITLE}}": escape(episode.english_title),
        "{{CHINESE_TITLE}}": escape(episode.chinese_title),
        "{{ACT_LINKS}}": act_links,
        "{{ACT_SECTIONS}}": act_sections,
        "{{PREVIOUS_LINK}}": previous_link,
        "{{NEXT_LINK}}": next_link,
    }
    page = _template("episode.html")
    for token, value in replacements.items():
        page = page.replace(token, value)
    if "{{" in page or "}}" in page:
        raise ValueError("Episode template contains an unreplaced token")
    return page
```

- [ ] **Step 5: Run renderer tests**

Run:

```bash
python3 -m unittest tests.test_render -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/render.py templates/ tests/test_render.py
git commit -m "Render semantic static reading pages."
```

## Task 7: Add The Paper-Script Responsive Design

**Files:**
- Create: `assets/styles.css`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Add failing stylesheet contract tests**

Add `from pathlib import Path` to the imports and add this method to
`RenderTest`:

```python
    def test_stylesheet_contains_required_responsive_contract(self):
        root = Path(__file__).resolve().parents[1]
        css = (root / "assets" / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".dialogue-line", css)
        self.assertIn(
            "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)",
            css,
        )
        self.assertIn("@media (max-width: 720px)", css)
        self.assertIn("grid-template-columns: 1fr", css)
        self.assertIn(
            '[data-chinese-hidden="true"] [data-chinese-text]',
            css,
        )
        self.assertIn(":focus-visible", css)
```

- [ ] **Step 2: Run the renderer tests**

Run:

```bash
python3 -m unittest tests.test_render -v
```

Expected: FAIL because `assets/styles.css` does not exist.

- [ ] **Step 3: Implement the complete visual system**

Create `assets/styles.css` with these required tokens and behaviors:

```css
:root {
  color-scheme: light;
  --paper: #f4eee2;
  --paper-raised: #fffaf1;
  --ink: #29231e;
  --muted: #6f655b;
  --accent: #91442f;
  --rule: #d8cdbd;
  --reading-width: 72rem;
  font-family: Georgia, "Times New Roman", serif;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  line-height: 1.65;
}
a { color: inherit; }
button, a { -webkit-tap-highlight-color: transparent; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }

.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: .8rem clamp(1rem, 4vw, 3rem);
  background: color-mix(in srgb, var(--paper-raised) 94%, transparent);
  border-bottom: 1px solid var(--rule);
}

.directory,
.episode-reader {
  width: min(calc(100% - 2rem), var(--reading-width));
  margin-inline: auto;
  padding-block: clamp(2rem, 6vw, 5rem);
}

.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: 1rem;
}

.dialogue-line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: clamp(1rem, 4vw, 3rem);
  padding-block: 1rem;
  border-bottom: 1px solid var(--rule);
}

.speaker,
.language-label,
.eyebrow {
  color: var(--accent);
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: .76rem;
  font-weight: 750;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.chinese-column {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
    system-ui, sans-serif;
}

[data-chinese-hidden="true"] [data-chinese-text] { display: none; }

@media (max-width: 720px) {
  .dialogue-line { grid-template-columns: 1fr; gap: .45rem; }
  .site-header { align-items: flex-start; }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
```

Complete the stylesheet with all classes emitted by both templates:
directory cards, title blocks, act navigation, toggle button, footer navigation,
hover states, and print rules. Keep body text at least `1rem` and touch targets
at least `44px` high.

- [ ] **Step 4: Run renderer tests**

Run:

```bash
python3 -m unittest tests.test_render -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add assets/styles.css tests/test_render.py
git commit -m "Style the responsive paper reading layout."
```

## Task 8: Add Progressive Chinese Visibility

**Files:**
- Create: `assets/reader.js`
- Create: `tests/test_reader_js.mjs`
- Modify: `templates/episode.html`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write failing JavaScript behavior tests**

```javascript
// tests/test_reader_js.mjs
import assert from "node:assert/strict";
import { readPreference, togglePreference } from "../assets/reader.js";

const storage = new Map();
const fakeStorage = {
  getItem(key) { return storage.has(key) ? storage.get(key) : null; },
  setItem(key, value) { storage.set(key, value); },
};

assert.equal(readPreference(fakeStorage), false);
assert.equal(togglePreference(fakeStorage, false), true);
assert.equal(fakeStorage.getItem("family-album-hide-chinese"), "true");
assert.equal(readPreference(fakeStorage), true);
assert.equal(togglePreference(fakeStorage, true), false);
assert.equal(fakeStorage.getItem("family-album-hide-chinese"), "false");

console.log("reader.js tests passed");
```

- [ ] **Step 2: Run the test and verify module failure**

Run:

```bash
node tests/test_reader_js.mjs
```

Expected: FAIL because `assets/reader.js` does not exist.

- [ ] **Step 3: Implement storage and DOM enhancement**

```javascript
// assets/reader.js
const STORAGE_KEY = "family-album-hide-chinese";

export function readPreference(storage) {
  return storage.getItem(STORAGE_KEY) === "true";
}

export function togglePreference(storage, current) {
  const next = !current;
  storage.setItem(STORAGE_KEY, String(next));
  return next;
}

function applyPreference(root, button, hidden) {
  root.dataset.chineseHidden = String(hidden);
  button.setAttribute("aria-pressed", String(hidden));
  button.textContent = hidden ? "显示中文" : "隐藏中文";
}

function enhanceReader() {
  const button = document.querySelector("[data-chinese-toggle]");
  if (!button) return;

  let hidden = readPreference(window.localStorage);
  applyPreference(document.documentElement, button, hidden);
  button.addEventListener("click", () => {
    hidden = togglePreference(window.localStorage, hidden);
    applyPreference(document.documentElement, button, hidden);
  });
}

if (typeof document !== "undefined") {
  enhanceReader();
}
```

Update the template button to:

```html
<button
  class="chinese-toggle"
  type="button"
  data-chinese-toggle
  aria-pressed="false"
>
  隐藏中文
</button>
```

Keep Chinese visible in raw HTML. Do not add an inline script that hides it
before the external module runs.

- [ ] **Step 4: Run JavaScript and renderer tests**

Run:

```bash
node tests/test_reader_js.mjs
python3 -m unittest tests.test_render -v
```

Expected: both commands pass.

- [ ] **Step 5: Commit**

```bash
git add assets/reader.js templates/episode.html tests/
git commit -m "Persist the Chinese visibility preference."
```

## Task 9: Generate And Validate The GitHub Pages Site

**Files:**
- Create: `scripts/build_site.py`
- Create: `tests/test_build_site.py`
- Generate: `docs/index.html`
- Generate: `docs/episode-01.html` through `docs/episode-26.html`
- Generate: `docs/assets/styles.css`
- Generate: `docs/assets/reader.js`
- Generate: `docs/CNAME`
- Generate: `docs/.nojekyll`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing generated-site tests**

```python
# tests/test_build_site.py
from html.parser import HTMLParser
from pathlib import Path
import unittest

from scripts.build_site import build_site, validate_site


ROOT = Path(__file__).resolve().parents[1]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


class BuildSiteTest(unittest.TestCase):
    def test_build_writes_complete_github_pages_output(self):
        build_site(ROOT / "data" / "episodes.json", ROOT / "docs")

        self.assertTrue((ROOT / "docs" / "index.html").is_file())
        self.assertEqual(
            len(list((ROOT / "docs").glob("episode-*.html"))),
            26,
        )
        self.assertEqual(
            (ROOT / "docs" / "CNAME").read_text(encoding="utf-8"),
            "usa.adihuang.com\n",
        )
        self.assertTrue((ROOT / "docs" / ".nojekyll").is_file())
        validate_site(ROOT / "docs")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test and verify import failure**

Run:

```bash
python3 -m unittest tests.test_build_site -v
```

Expected: FAIL because `scripts.build_site` does not exist.

- [ ] **Step 3: Implement deterministic site generation**

Create `scripts/build_site.py` with these interfaces:

```python
from argparse import ArgumentParser
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil

from scripts.models import Act, Correction, DialogueLine, Episode
from scripts.render import render_episode_page, render_index_page


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.sources: list[str] = []
        self.ids: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag in {"script", "link"}:
            source = values.get("src") or values.get("href")
            if source:
                self.sources.append(source)


def load_episodes(path: Path) -> list[Episode]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    episodes = []
    for episode_data in payload:
        acts = []
        for act_data in episode_data["acts"]:
            lines = []
            for line_data in act_data["lines"]:
                corrections = [
                    Correction(**correction)
                    for correction in line_data["corrections"]
                ]
                lines.append(
                    DialogueLine(
                        speaker=line_data["speaker"],
                        english=line_data["english"],
                        chinese=line_data["chinese"],
                        source_paragraphs=line_data["source_paragraphs"],
                        corrections=corrections,
                    )
                )
            acts.append(Act(number=act_data["number"], lines=lines))
        episodes.append(
            Episode(
                number=episode_data["number"],
                english_title=episode_data["english_title"],
                chinese_title=episode_data["chinese_title"],
                acts=acts,
            )
        )
    return episodes


def build_site(data_path: Path, output_dir: Path) -> None:
    episodes = load_episodes(data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob("episode-*.html"):
        path.unlink()
    assets_output = output_dir / "assets"
    if assets_output.exists():
        shutil.rmtree(assets_output)
    assets_output.mkdir()

    (output_dir / "index.html").write_text(
        render_index_page(episodes),
        encoding="utf-8",
    )
    for index, episode in enumerate(episodes):
        previous = episodes[index - 1] if index else None
        following = episodes[index + 1] if index + 1 < len(episodes) else None
        (output_dir / f"episode-{episode.number:02d}.html").write_text(
            render_episode_page(episode, previous, following),
            encoding="utf-8",
        )

    root = Path(__file__).resolve().parents[1]
    shutil.copy2(root / "assets" / "styles.css", assets_output / "styles.css")
    shutil.copy2(root / "assets" / "reader.js", assets_output / "reader.js")
    (output_dir / "CNAME").write_text("usa.adihuang.com\n", encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    validate_site(output_dir)


def validate_site(output_dir: Path) -> None:
    episode_pages = sorted(output_dir.glob("episode-*.html"))
    if len(episode_pages) != 26:
        raise ValueError("Expected exactly 26 generated episode pages")

    pages = [output_dir / "index.html", *episode_pages]
    for page in pages:
        parser = SiteParser()
        parser.feed(page.read_text(encoding="utf-8"))
        if len(parser.ids) != len(set(parser.ids)):
            raise ValueError(f"Duplicate HTML id in {page.name}")
        for target in [*parser.links, *parser.sources]:
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part, _, fragment = target.partition("#")
            target_path = output_dir / path_part
            if not target_path.exists():
                raise ValueError(
                    f"Broken local target in {page.name}: {target}"
                )
            if fragment and target_path.suffix == ".html":
                target_parser = SiteParser()
                target_parser.feed(target_path.read_text(encoding="utf-8"))
                if fragment not in target_parser.ids:
                    raise ValueError(
                        f"Missing fragment in {target}: {fragment}"
                    )


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("data_path", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_site(args.data_path, args.output_dir)


if __name__ == "__main__":
    main()
```

This deliberately removes only known generated episode files and the generated
asset directory. It does not remove unknown files from `docs/`.

- [ ] **Step 4: Run generated-site tests**

Run:

```bash
python3 -m unittest tests.test_build_site -v
```

Expected: all tests pass.

- [ ] **Step 5: Document exact build and verification commands**

Replace the final paragraph under `## Validation` in `CLAUDE.md` with:

````markdown
Run:

```bash
python3 -m scripts.build_content \
  "source/走遍美国中英文对照.docx" \
  --output-dir data
python3 -m scripts.build_site data/episodes.json --output-dir docs
python3 -m unittest discover -s tests -v
node tests/test_reader_js.mjs
```
````

- [ ] **Step 6: Run the complete build twice and verify determinism**

Run:

```bash
python3 -m scripts.build_content \
  "source/走遍美国中英文对照.docx" \
  --output-dir data
python3 -m scripts.build_site data/episodes.json --output-dir docs
git diff -- data docs > /tmp/family-album-first.diff
python3 -m scripts.build_content \
  "source/走遍美国中英文对照.docx" \
  --output-dir data
python3 -m scripts.build_site data/episodes.json --output-dir docs
git diff -- data docs > /tmp/family-album-second.diff
cmp /tmp/family-album-first.diff /tmp/family-album-second.diff
```

Expected: `cmp` exits 0.

- [ ] **Step 7: Run the complete automated verification**

Run:

```bash
python3 -m unittest discover -s tests -v
node tests/test_reader_js.mjs
git diff --check
```

Expected: all tests pass and `git diff --check` emits no output.

- [ ] **Step 8: Commit**

```bash
git add CLAUDE.md scripts/build_site.py tests/test_build_site.py data/ docs/
git commit -m "Generate the complete GitHub Pages site."
```

## Task 10: Perform Browser And Accessibility Verification

**Files:**
- Review and modify on a failing regression test: `assets/styles.css`
- Review and modify on a failing regression test: `assets/reader.js`
- Review and modify on a failing regression test: `templates/index.html`
- Review and modify on a failing regression test: `templates/episode.html`
- Regenerate: `docs/`

- [ ] **Step 1: Start a local static server**

Run:

```bash
python3 -m http.server 8000 --directory docs
```

Expected: server listens at `http://localhost:8000/`.

- [ ] **Step 2: Verify representative pages with Browser**

Use the in-app Browser plugin and inspect:

```text
http://localhost:8000/
http://localhost:8000/episode-01.html
http://localhost:8000/episode-13.html
http://localhost:8000/episode-26.html
```

Check:

- directory cards are legible and link correctly;
- desktop dialogue is paired in two columns;
- mobile dialogue stacks Chinese below English;
- header controls remain touch-friendly;
- Act anchors land on the correct sections;
- first/middle/final previous-next navigation is correct;
- Chinese visibility persists across page loads;
- raw HTML remains bilingual with JavaScript disabled;
- keyboard focus is visible;
- 200 percent zoom does not introduce horizontal scrolling;
- no text overlaps or clips.

- [ ] **Step 3: Fix only observed defects and add regression tests**

For each observed defect:

1. Add or extend a test under `tests/test_render.py`,
   `tests/test_build_site.py`, or `tests/test_reader_js.mjs`.
2. Verify the new test fails.
3. Apply the smallest template, CSS, or JavaScript fix.
4. Rebuild `docs/`.
5. Verify the test passes and repeat the browser check.

- [ ] **Step 4: Run final verification**

Run:

```bash
python3 -m scripts.build_content \
  "source/走遍美国中英文对照.docx" \
  --output-dir data
python3 -m scripts.build_site data/episodes.json --output-dir docs
python3 -m unittest discover -s tests -v
node tests/test_reader_js.mjs
git diff --check
git status --short
```

Expected: all tests pass, no whitespace errors exist, and only intended
generated or source changes appear.

- [ ] **Step 5: Commit browser-verified refinements**

If files changed during visual QA:

```bash
git add assets/ templates/ tests/ docs/
git commit -m "Refine the verified reading experience."
```

If no files changed, do not create an empty commit.

## Task 11: Configure GitHub Pages Without Publishing

**Files:**
- No repository file changes expected beyond the generated `docs/CNAME`.

- [ ] **Step 1: Confirm repository ownership information**

Determine the GitHub repository owner and repository URL from:

```bash
git remote -v
```

Expected: an `origin` URL identifying the GitHub Pages CNAME target
`<owner>.github.io`.

- [ ] **Step 2: Stop at the publication red line**

Do not push, configure DNS, or enable GitHub Pages until the user explicitly
approves publication actions.

Present these exact pending actions:

```text
1. Push the committed branch to GitHub.
2. Configure GitHub Pages to publish from /docs on the selected branch.
3. Add DNS CNAME: usa -> <owner>.github.io.
4. Set the Pages custom domain to usa.adihuang.com.
5. Enable HTTPS after certificate provisioning.
```

- [ ] **Step 3: After approval, publish and verify**

Only after explicit approval:

```bash
git push -u origin main
```

Configure GitHub Pages and DNS through the appropriate authenticated interface.
Then verify:

```bash
curl -I https://usa.adihuang.com/
```

Expected after DNS and certificate propagation: HTTP 200 or a normal redirect
to an HTTPS 200 response.

- [ ] **Step 4: Verify the deployed site**

Open:

```text
https://usa.adihuang.com/
https://usa.adihuang.com/episode-01.html
https://usa.adihuang.com/episode-26.html
```

Repeat the key navigation, responsive layout, and Chinese visibility checks.
No additional commit is required unless deployment verification reveals a
repository defect.
