import unittest

from scripts.docx_reader import Paragraph, Run
from scripts.normalize import (
    SPEAKER_CORRECTIONS,
    CleanupIssue,
    normalize_document,
)


def paragraph(number: int, text: str, color: str | None = None) -> Paragraph:
    return Paragraph(number=number, text=text, runs=[Run(text=text, color=color)])


def complete_episode(*act_one_paragraphs: Paragraph) -> list[Paragraph]:
    next_number = max(
        (item.number for item in act_one_paragraphs),
        default=2,
    ) + 1
    return [
        paragraph(1, "EPISODE 1 46 Linden Street林登大街 46 号"),
        paragraph(2, "Act 1."),
        *act_one_paragraphs,
        paragraph(next_number, "Act 2."),
        paragraph(next_number + 1, "Richard： Thanks.谢谢。"),
        paragraph(next_number + 2, "Act 3."),
        paragraph(next_number + 3, "Richard： Bye.再见。"),
    ]


class CleanupIssueTest(unittest.TestCase):
    def test_is_frozen_and_serializes_to_dict(self):
        issue = CleanupIssue(
            episode=1,
            act=2,
            source_paragraphs=[12],
            category="suspected-typo",
            source_text="yuo",
            detail="Preserved because the intended correction is uncertain",
            confidence="uncertain",
        )

        self.assertEqual(
            issue.to_dict(),
            {
                "episode": 1,
                "act": 2,
                "source_paragraphs": [12],
                "category": "suspected-typo",
                "source_text": "yuo",
                "detail": (
                    "Preserved because the intended correction is uncertain"
                ),
                "confidence": "uncertain",
            },
        )
        with self.assertRaises(AttributeError):
            issue.category = "changed"  # type: ignore[misc]


class NormalizeDocumentTest(unittest.TestCase):
    def test_discards_front_matter_and_applies_certain_corrections(self):
        source = [
            paragraph(1, "EPISODE 1 Contents目录"),
            paragraph(2, "Richard： red means speaker", "FF0000"),
            paragraph(3, "EPISODE 1 46 Linden Street林登大街 46 号"),
            paragraph(4, "Act1."),
            paragraph(5, "Alexadra： Excue me.对不起。", "FF0000"),
            paragraph(6, "Act 2."),
            paragraph(7, "Richard： What's it for?做什么用？"),
            paragraph(8, "Act 3."),
            paragraph(9, "Richard： Thank you.谢谢。"),
        ]

        episodes, issues = normalize_document(source)

        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].number, 1)
        self.assertEqual(episodes[0].english_title, "46 Linden Street")
        self.assertEqual(episodes[0].chinese_title, "林登大街 46 号")
        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.speaker, "Alexandra")
        self.assertEqual(line.english, "Excuse me.")
        self.assertEqual(line.chinese, "对不起。")
        self.assertEqual(
            [correction.category for correction in line.corrections],
            ["speaker", "spelling"],
        )
        self.assertEqual(issues, [])

    def test_merges_continuation_without_bad_spacing(self):
        source = complete_episode(
            paragraph(3, "Harry： Can I speak"),
            paragraph(4, "to Betty?我能跟 Betty"),
            paragraph(5, "说话吗？"),
        )

        episodes, issues = normalize_document(source)

        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.english, "Can I speak to Betty?")
        self.assertEqual(line.chinese, "我能跟 Betty说话吗？")
        self.assertEqual(line.source_paragraphs, [3, 4, 5])
        self.assertEqual(issues, [])

    def test_joins_continuation_punctuation_and_hyphen_without_extra_space(self):
        source = complete_episode(
            paragraph(3, "Harry： Is this"),
            paragraph(4, "?这是"),
            paragraph(5, "well-"),
            paragraph(6, "known?众所周知的吗？"),
        )

        episodes, _ = normalize_document(source)

        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.english, "Is this? well-known?")
        self.assertEqual(line.chinese, "这是众所周知的吗？")

    def test_supports_all_explicit_speaker_corrections(self):
        for misspelling, expected in {
            "Alexadra": "Alexandra",
            "Alexanra": "Alexandra",
            "Marllyn": "Marilyn",
        }.items():
            with self.subTest(misspelling=misspelling):
                self.assertEqual(SPEAKER_CORRECTIONS[misspelling], expected)
                episodes, _ = normalize_document(
                    complete_episode(
                        paragraph(3, f"{misspelling}； Hello.你好。"),
                    )
                )
                self.assertEqual(
                    episodes[0].acts[0].lines[0].speaker,
                    expected,
                )

    def test_supports_compact_act_headings(self):
        source = [
            paragraph(1, "Episode 1 First第一集"),
            paragraph(2, "Act1."),
            paragraph(3, "Richard： One.一。"),
            paragraph(4, "Act2."),
            paragraph(5, "Richard; Two.二。"),
            paragraph(6, "Act3."),
            paragraph(7, "Richard： Three.三。"),
        ]

        episodes, issues = normalize_document(source)

        self.assertEqual([act.number for act in episodes[0].acts], [1, 2, 3])
        self.assertEqual(issues, [])

    def test_preserves_uncertain_yuo_and_reports_issue(self):
        source = complete_episode(
            paragraph(3, "Richard： Are yuo from Florida?你来自佛罗里达吗？"),
        )

        episodes, issues = normalize_document(source)

        self.assertEqual(
            episodes[0].acts[0].lines[0].english,
            "Are yuo from Florida?",
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].category, "suspected-typo")
        self.assertEqual(issues[0].source_paragraphs, [3])

    def test_reports_missing_chinese(self):
        source = complete_episode(
            paragraph(3, "Richard： English only."),
        )

        _, issues = normalize_document(source)

        self.assertEqual(
            [issue.category for issue in issues],
            ["missing-chinese"],
        )
        self.assertEqual(issues[0].source_text, "English only.")

    def test_reports_paragraph_without_receiving_dialogue(self):
        source = complete_episode(
            paragraph(3, "Philip says hello.菲利普打招呼。"),
            paragraph(4, "Richard： Hello.你好。"),
            paragraph(5, "Marilyn missing delimiter.玛丽琳缺少分隔符。"),
        )

        episodes, issues = normalize_document(source)

        self.assertEqual(len(episodes[0].acts[0].lines), 1)
        self.assertEqual(
            [issue.category for issue in issues],
            ["unassigned-continuation", "unassigned-continuation"],
        )
        self.assertEqual(
            [issue.source_paragraphs for issue in issues],
            [[3], [5]],
        )

    def test_does_not_guess_uppercase_text_after_missing_chinese(self):
        source = complete_episode(
            paragraph(3, "Richard： English only."),
            paragraph(4, "Philip missing delimiter.菲利普缺少分隔符。"),
        )

        episodes, issues = normalize_document(source)

        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.english, "English only.")
        self.assertEqual(line.source_paragraphs, [3])
        self.assertEqual(
            [issue.category for issue in issues],
            ["unassigned-continuation", "missing-chinese"],
        )

    def test_applies_text_correction_in_continuation(self):
        source = complete_episode(
            paragraph(3, "Richard： I come from"),
            paragraph(4, "northem Greece.我来自希腊北部。"),
        )

        episodes, issues = normalize_document(source)

        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.english, "I come from northern Greece.")
        self.assertEqual(len(line.corrections), 1)
        self.assertEqual(line.corrections[0].before, "northem Greece")
        self.assertEqual(line.corrections[0].after, "northern Greece")
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
