from dataclasses import asdict, dataclass
import re
from typing import Any

from scripts.docx_reader import Paragraph
from scripts.models import Act, Correction, DialogueLine, Episode


@dataclass(frozen=True)
class CleanupIssue:
    episode: int | None
    act: int | None
    source_paragraphs: tuple[int, ...]
    category: str
    source_text: str
    detail: str
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_paragraphs"] = list(self.source_paragraphs)
        return value


SPEAKER_CORRECTIONS = {
    "Alexadra": "Alexandra",
    "Alexanra": "Alexandra",
    "Marllyn": "Marilyn",
    "Jcak": "Jack",
    "Rbbie": "Robbie",
    "Phinip": "Philip",
    "Granpa": "Grandpa",
    "Alexcandra": "Alexandra",
    "RIchard": "Richard",
}

TEXT_CORRECTIONS = {
    "Excue me.": "Excuse me.",
    "northem Greece": "northern Greece",
    "Jcak": "Jack",
    "Rbbie": "Robbie",
    "Phinip": "Philip",
    "Granpa": "Grandpa",
    "Alexcandra": "Alexandra",
    "RIchard": "Richard",
}

TITLE_CORRECTIONS = {
    "Me's Bast Friend": "Man's Best Friend",
    "You're Goingto Be Fine": "You're Going to Be Fine",
    "Making Difference": "Making a Difference",
}

ACT_BOUNDARY_OVERRIDES = {
    (3, 427): 2,
}

KNOWN_SPEAKERS = frozenset(
    {
        "Abe",
        "Albert",
        "Alexandra",
        "Allen",
        "Amold",
        "Attendant",
        "Audrey",
        "Betty",
        "Bill",
        "Boswell",
        "Carl",
        "Carlson",
        "Clerk",
        "Conductor",
        "Customer",
        "Danny",
        "Dean",
        "Ellen",
        "Ellen&Philip",
        "Elsa",
        "Father",
        "Frank",
        "Gerald",
        "Girls",
        "Grandpa",
        "Harry",
        "Harry&Michelle",
        "Innkeeper",
        "Instructor",
        "Jack",
        "Jimmy",
        "Joanne",
        "Judge",
        "Lillian",
        "Linda",
        "Marchetta",
        "Marilyn",
        "Marilyn&Michelle",
        "Maxwell",
        "Michelle",
        "Mike",
        "Millie",
        "Mitchell",
        "Molly",
        "Mother",
        "Mr. Riley",
        "Mr.Riley",
        "Mrs.Vann",
        "Nat",
        "O'Neill",
        "Operator",
        "Peggy",
        "Pete",
        "Philip",
        "Policeman",
        "Receptionist",
        "Reporter",
        "Richard",
        "Richard&Robbie",
        "Rita Mae",
        "Robbie",
        "Sam",
        "Sandra",
        "Shirley",
        "Somsak",
        "Susan",
        "Tim",
        "Tom",
        "Vendor",
        "Virginia",
        "Voice",
        "Waiter",
        "Woman",
        "Worker",
    }
)
SPEAKER_ALIASES = KNOWN_SPEAKERS | frozenset(SPEAKER_CORRECTIONS)

EPISODE_PATTERN = re.compile(r"^episode\s+(\d+)\s*(.*)$", re.IGNORECASE)
ACT_PATTERN = re.compile(r"^act\s*([123])\s*\.?$", re.IGNORECASE)
SPEAKER_DELIMITERS = ":：;；"
SPEAKER_PREFIX_PATTERN = re.compile(
    rf"^([^{SPEAKER_DELIMITERS}]{{1,32}})"
    rf"[{SPEAKER_DELIMITERS}]\s*"
)
SPEAKER_NAME_PATTERN = re.compile(
    r"^(?:Mr\.?\s+|Mrs\.?\s+|Ms\.?\s+)?"
    r"[A-Z][A-Za-z]*(?:[.'-][A-Za-z]+)*"
    r"(?:\s+[A-Z][A-Za-z]*(?:[.'-][A-Za-z]+)*)?$"
)
SPEAKER_MARKER_PATTERN = re.compile(
    rf"(?<![\w'])"
    rf"({'|'.join(re.escape(name) for name in sorted(SPEAKER_ALIASES, key=len, reverse=True))})"
    rf"\s*[{SPEAKER_DELIMITERS}]\s*"
)
CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")
SPACE_PATTERN = re.compile(r"\s+")
SUSPECT_PATTERNS = (re.compile(r"\byuo\b", re.IGNORECASE),)
NO_LEADING_SPACE_PATTERN = re.compile(r"""^[,.;:!?%)\]}'"”’]""")
SENTENCE_END_PATTERN = re.compile(r"[.!?]\s+$")
CHINESE_LINE_BREAK_PATTERN = re.compile(r"(?<=[。！？?])\s+")


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


def _known_speaker(name: str) -> bool:
    normalized = SPACE_PATTERN.sub(" ", name).strip()
    return normalized in SPEAKER_ALIASES


def _reasonable_speaker(name: str) -> bool:
    normalized = SPACE_PATTERN.sub(" ", name).strip()
    return SPEAKER_NAME_PATTERN.fullmatch(normalized) is not None


def _initial_speaker(paragraph: Paragraph, english: str) -> str | None:
    first_run = next(
        (run.text.strip() for run in paragraph.runs if run.text.strip()),
        "",
    )
    if first_run.endswith(tuple(SPEAKER_DELIMITERS)):
        run_speaker = first_run[:-1].strip()
        if _known_speaker(run_speaker) or _reasonable_speaker(run_speaker):
            return run_speaker

    prefix_match = SPEAKER_PREFIX_PATTERN.match(english)
    if prefix_match is None:
        return None
    candidate = prefix_match.group(1).strip()
    return candidate if _known_speaker(candidate) else None


def _speaker_markers(english: str, initial_speaker: str) -> list[re.Match[str]]:
    initial_match = SPEAKER_PREFIX_PATTERN.match(english)
    if (
        initial_match is None
        or initial_match.group(1).strip() != initial_speaker
    ):
        return []

    markers = [initial_match]
    for match in SPEAKER_MARKER_PATTERN.finditer(english):
        if match.start() == 0:
            continue
        if SENTENCE_END_PATTERN.search(english[: match.start()]):
            markers.append(match)
    return markers


def _split_chinese_lines(chinese: str, line_count: int) -> list[str]:
    if line_count == 1:
        return [chinese]
    if not chinese:
        return [""] * line_count

    parts = [
        part.strip()
        for part in CHINESE_LINE_BREAK_PATTERN.split(chinese)
        if part.strip()
    ]
    if len(parts) == line_count:
        return parts
    return [chinese, *([""] * (line_count - 1))]


def _dialogue_lines(paragraph: Paragraph) -> list[DialogueLine]:
    english, chinese = _split_languages(paragraph.text)
    initial_speaker = _initial_speaker(paragraph, english)
    if initial_speaker is None:
        return []

    markers = _speaker_markers(english, initial_speaker)
    if not markers:
        return []

    chinese_lines = _split_chinese_lines(chinese, len(markers))
    lines = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else None
        speaker, speaker_corrections = _normalize_speaker(marker.group(1))
        text, text_corrections = _normalize_text(english[marker.end() : end])
        lines.append(
            DialogueLine(
                speaker=speaker,
                english=text,
                chinese=chinese_lines[index],
                source_paragraphs=[paragraph.number],
                corrections=speaker_corrections + text_corrections,
            )
        )
    return lines


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
            source_paragraphs=(paragraph.number,),
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
        source_paragraphs=(paragraph.number,),
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
            corrected_title = TITLE_CORRECTIONS.get(
                english_title,
                english_title,
            )
            if corrected_title != english_title:
                issues.append(
                    CleanupIssue(
                        episode=number,
                        act=None,
                        source_paragraphs=(paragraph.number,),
                        category="corrected-title",
                        source_text=english_title,
                        detail=(
                            f"Corrected title from {english_title!r} "
                            f"to {corrected_title!r}"
                        ),
                        confidence="certain",
                    )
                )
            current_episode = Episode(
                number=number,
                english_title=corrected_title,
                chinese_title=chinese_title,
                acts=[],
            )
            episodes.append(current_episode)
            current_act = None
            current_line = None
            continue

        if current_episode is not None:
            override_number = ACT_BOUNDARY_OVERRIDES.get(
                (current_episode.number, paragraph.number)
            )
            if override_number is not None:
                current_act = Act(number=override_number, lines=[])
                current_episode.acts.append(current_act)
                current_line = None
                issues.append(
                    CleanupIssue(
                        episode=current_episode.number,
                        act=override_number,
                        source_paragraphs=(paragraph.number,),
                        category="inserted-act-boundary",
                        source_text=paragraph.text,
                        detail="Inserted deterministic missing act boundary",
                        confidence="certain",
                    )
                )

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
                    source_paragraphs=(paragraph.number,),
                    category="orphan-paragraph",
                    source_text=paragraph.text,
                    detail="Paragraph appears outside an episode act",
                    confidence="certain",
                )
            )
            continue

        dialogue_lines = _dialogue_lines(paragraph)
        if dialogue_lines:
            current_act.lines.extend(dialogue_lines)
            current_line = dialogue_lines[-1]
            _record_suspect_text(
                issues,
                current_episode.number,
                current_act.number,
                paragraph,
            )
            continue

        if current_line is None:
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
                        source_paragraphs=tuple(line.source_paragraphs),
                        category="missing-chinese",
                        source_text=line.english,
                        detail="No Chinese translation was found",
                        confidence="certain",
                    )
                )

    return episodes, issues
