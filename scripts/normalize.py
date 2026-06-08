from dataclasses import asdict, dataclass
import re
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
SPEAKER_PATTERN = re.compile(r"^([^:：;；]{1,32})[:：;；]\s*(.*)$")
CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")
SPACE_PATTERN = re.compile(r"\s+")
SUSPECT_PATTERNS = (re.compile(r"\byuo\b", re.IGNORECASE),)
NO_LEADING_SPACE_PATTERN = re.compile(r"""^[,.;:!?%)\]}'"”’]""")
CONTINUATION_START_PATTERN = re.compile(
    r"""^(?:[a-z]|[,.;:!?%)\]}'"”’]|[\u3400-\u9fff])"""
)


def _content_start(paragraphs: list[Paragraph]) -> int:
    candidates = [
        index
        for index, paragraph in enumerate(paragraphs)
        if re.match(
            r"^episode\s+1(?:\D|$)",
            paragraph.text.strip(),
            re.IGNORECASE,
        )
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
    cjk_match = CJK_PATTERN.search(title)
    if cjk_match is None:
        return number, title, ""
    return (
        number,
        title[: cjk_match.start()].strip(),
        title[cjk_match.start() :].strip(),
    )


def _split_languages(text: str) -> tuple[str, str]:
    cjk_match = CJK_PATTERN.search(text)
    if cjk_match is None:
        return text.strip(), ""
    return (
        text[: cjk_match.start()].strip(),
        text[cjk_match.start() :].strip(),
    )


def _normalize_speaker(name: str) -> tuple[str, list[Correction]]:
    before = SPACE_PATTERN.sub(" ", name).strip()
    after = SPEAKER_CORRECTIONS.get(before, before)
    if before == after:
        return after, []
    return after, [
        Correction(
            category="speaker",
            before=before,
            after=after,
            confidence="certain",
        )
    ]


def _normalize_text(text: str) -> tuple[str, list[Correction]]:
    value = SPACE_PATTERN.sub(" ", text).strip()
    corrections = []
    for before, after in TEXT_CORRECTIONS.items():
        if before not in value:
            continue
        value = value.replace(before, after)
        corrections.append(
            Correction(
                category="spelling",
                before=before,
                after=after,
                confidence="certain",
            )
        )
    return value, corrections


def _join_english(left: str, right: str) -> str:
    left = left.rstrip()
    right = right.lstrip()
    if not left:
        return right
    if not right:
        return left
    if left.endswith("-") or NO_LEADING_SPACE_PATTERN.match(right):
        return f"{left}{right}"
    return f"{left} {right}"


def _join_chinese(left: str, right: str) -> str:
    left = left.rstrip()
    right = right.lstrip()
    if not left:
        return right
    if not right:
        return left
    if left[-1].isascii() and left[-1].isalnum():
        if right[0].isascii() and right[0].isalnum():
            return f"{left} {right}"
    return f"{left}{right}"


def _append_continuation(
    line: DialogueLine,
    paragraph: Paragraph,
) -> None:
    english, chinese = _split_languages(paragraph.text)
    english, corrections = _normalize_text(english)
    line.english = _join_english(line.english, english)
    line.chinese = _join_chinese(line.chinese, chinese)
    line.source_paragraphs.append(paragraph.number)
    line.corrections.extend(corrections)


def _can_append_continuation(
    line: DialogueLine | None,
    paragraph: Paragraph,
) -> bool:
    if line is None:
        return False
    return CONTINUATION_START_PATTERN.match(paragraph.text.strip()) is not None


def _record_suspect_text(
    issues: list[CleanupIssue],
    episode: int,
    act: int,
    paragraph: Paragraph,
) -> None:
    if not any(pattern.search(paragraph.text) for pattern in SUSPECT_PATTERNS):
        return
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


def _unassigned_issue(
    episode: int,
    act: int,
    paragraph: Paragraph,
) -> CleanupIssue:
    return CleanupIssue(
        episode=episode,
        act=act,
        source_paragraphs=[paragraph.number],
        category="unassigned-continuation",
        source_text=paragraph.text,
        detail="No preceding dialogue reliably accepts this continuation",
        confidence="uncertain",
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
        if EPISODE_PATTERN.match(paragraph.text.strip()):
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

        act_match = ACT_PATTERN.match(paragraph.text.strip())
        if act_match is not None:
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

        speaker_match = SPEAKER_PATTERN.match(paragraph.text.strip())
        if speaker_match is not None:
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

        if not _can_append_continuation(current_line, paragraph):
            issues.append(
                _unassigned_issue(
                    current_episode.number,
                    current_act.number,
                    paragraph,
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
                if line.chinese:
                    continue
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
