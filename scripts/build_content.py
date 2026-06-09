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
    del issues
    if [episode.number for episode in episodes] != list(range(1, 27)):
        raise ValueError("Expected sequential episodes 1 through 26")

    for episode in episodes:
        if [act.number for act in episode.acts] != [1, 2, 3]:
            raise ValueError(
                f"Episode {episode.number} must contain acts 1, 2, 3"
            )
        for act in episode.acts:
            for line in act.lines:
                if not line.speaker or not line.english:
                    raise ValueError(
                        f"Episode {episode.number} act {act.number} "
                        "contains dialogue without speaker or English text"
                    )


def _corrections(episodes: list[Episode]) -> list[dict[str, object]]:
    return [
        {
            "episode": episode.number,
            "act": act.number,
            "speaker": line.speaker,
            "source_paragraphs": list(line.source_paragraphs),
            **correction.to_dict(),
        }
        for episode in episodes
        for act in episode.acts
        for line in act.lines
        for correction in line.corrections
    ]


def _applied_issues(
    issues: list[CleanupIssue],
) -> list[dict[str, object]]:
    return [
        issue.to_dict()
        for issue in issues
        if issue.confidence == "certain"
        and issue.category != "missing-chinese"
    ]


def _unresolved_issues(
    issues: list[CleanupIssue],
) -> list[dict[str, object]]:
    return [
        issue.to_dict()
        for issue in issues
        if issue.confidence != "certain"
        or issue.category == "missing-chinese"
    ]


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_content(
    source: Path,
    output_dir: Path | None = None,
) -> tuple[list[Episode], list[CleanupIssue]]:
    episodes, issues = normalize_document(read_paragraphs(source))
    validate_episodes(episodes, issues)

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_json(
            output_dir / "episodes.json",
            [episode.to_dict() for episode in episodes],
        )
        _write_json(
            output_dir / "cleanup-report.json",
            {
                "corrections": [
                    *_corrections(episodes),
                    *_applied_issues(issues),
                ],
                "unresolved": _unresolved_issues(issues),
            },
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
