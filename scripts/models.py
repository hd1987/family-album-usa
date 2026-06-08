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
            "corrections": [
                correction.to_dict() for correction in self.corrections
            ],
        }


@dataclass
class Act:
    number: int
    lines: list[DialogueLine]

    def __post_init__(self) -> None:
        if self.number not in (1, 2, 3):
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
