from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from scripts.docx_reader import Paragraph, Run, read_paragraphs
from scripts.normalize import (
    ACT_BOUNDARY_OVERRIDES,
    SPEAKER_CORRECTIONS,
    CleanupIssue,
    normalize_document,
)


SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "source"
    / "走遍美国中英文对照.docx"
)


def paragraph(number: int, text: str, color: str | None = None) -> Paragraph:
    return Paragraph(number=number, text=text, runs=[Run(text=text, color=color)])


def real_paragraphs(*numbers: int) -> list[Paragraph]:
    wanted = set(numbers)
    return [
        item
        for item in read_paragraphs(SOURCE_PATH)
        if item.number in wanted
    ]


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
            source_paragraphs=(12,),
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
        self.assertEqual(issue.source_paragraphs, (12,))
        with self.assertRaises(FrozenInstanceError):
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
            "Jcak": "Jack",
            "Rbbie": "Robbie",
            "Phinip": "Philip",
            "Granpa": "Grandpa",
            "Alexcandra": "Alexandra",
            "RIchard": "Richard",
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
                correction = episodes[0].acts[0].lines[0].corrections[0]
                self.assertEqual(correction.category, "speaker")
                self.assertEqual(correction.before, misspelling)
                self.assertEqual(correction.after, expected)

    def test_records_real_speaker_corrections(self):
        cases = {
            590: ("Jcak", "Jack"),
            737: ("Rbbie", "Robbie"),
            820: ("Phinip", "Philip"),
            1073: ("Alexcandra", "Alexandra"),
            1699: ("RIchard", "Richard"),
            1955: ("Granpa", "Grandpa"),
        }

        for number, (before, after) in cases.items():
            with self.subTest(paragraph=number):
                episodes, _ = normalize_document(
                    complete_episode(*real_paragraphs(number))
                )
                line = episodes[0].acts[0].lines[0]
                self.assertEqual(line.speaker, after)
                self.assertTrue(
                    any(
                        correction.category == "speaker"
                        and correction.before == before
                        and correction.after == after
                        for correction in line.corrections
                    )
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

    def test_accepts_reasonable_name_in_standalone_speaker_run(self):
        source = complete_episode(
            Paragraph(
                number=3,
                text="Newman： Hello.你好。",
                runs=[
                    Run(text="Newman：", color="123456"),
                    Run(text=" Hello.", color=None),
                    Run(text="你好。", color=None),
                ],
            )
        )

        episodes, issues = normalize_document(source)

        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.speaker, "Newman")
        self.assertEqual(line.english, "Hello.")
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
        self.assertEqual(issues[0].source_paragraphs, (3,))

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
        )

        episodes, issues = normalize_document(source)

        self.assertEqual(len(episodes[0].acts[0].lines), 1)
        self.assertEqual(
            [issue.category for issue in issues],
            ["unassigned-continuation"],
        )
        self.assertEqual(
            [issue.source_paragraphs for issue in issues],
            [(3,)],
        )

    def test_merges_uppercase_continuation_after_missing_chinese(self):
        source = complete_episode(
            paragraph(3, "Richard： English only."),
            paragraph(4, "Will you forgive me?你能原谅我吗？"),
        )

        episodes, issues = normalize_document(source)

        line = episodes[0].acts[0].lines[0]
        self.assertEqual(line.english, "English only. Will you forgive me?")
        self.assertEqual(line.chinese, "你能原谅我吗？")
        self.assertEqual(line.source_paragraphs, [3, 4])
        self.assertEqual(issues, [])

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

    def test_merges_real_uppercase_continuations(self):
        real = real_paragraphs(298, 299, 571, 572)
        source = [
            paragraph(1, "Episode 1 Real Continuations真实续行"),
            paragraph(2, "Act 1."),
            *real[:2],
            paragraph(300, "Act 2."),
            *real[2:],
            paragraph(573, "Act 3."),
            paragraph(574, "Richard： Done.完成。"),
        ]

        episodes, _ = normalize_document(source)

        act_one_line = episodes[0].acts[0].lines[0]
        act_two_line = episodes[0].acts[1].lines[0]
        self.assertIn("Will you forgive me?", act_one_line.english)
        self.assertIn("Good, it's 122 over 80.", act_two_line.english)
        self.assertIn(299, act_one_line.source_paragraphs)
        self.assertIn(572, act_two_line.source_paragraphs)

    def test_inserts_real_episode_three_act_two_boundary(self):
        source = [
            paragraph(1, "Episode 1 Placeholder占位"),
            paragraph(2, "Act 1."),
            paragraph(3, "Richard： Placeholder.占位。"),
            paragraph(4, "Act 2."),
            paragraph(5, "Richard： Placeholder.占位。"),
            paragraph(6, "Act 3."),
            paragraph(7, "Richard： Placeholder.占位。"),
            *real_paragraphs(373, 374, 426, 427, 428, 481, 482),
        ]

        episodes, issues = normalize_document(source)

        episode = episodes[1]
        self.assertEqual(ACT_BOUNDARY_OVERRIDES[(3, 427)], 2)
        self.assertEqual([act.number for act in episode.acts], [1, 2, 3])
        self.assertEqual(episode.acts[0].lines[-1].speaker, "Philip")
        self.assertEqual(episode.acts[1].lines[0].speaker, "Elsa")
        boundary_issue = next(
            issue for issue in issues if issue.category == "inserted-act-boundary"
        )
        self.assertEqual(boundary_issue.source_paragraphs, (427,))

    def test_real_body_colons_are_not_speakers(self):
        misleading = real_paragraphs(613, 1185, 1900)

        for item, false_speaker in zip(
            misleading,
            ("salad", "Time", "Let's see. Name"),
            strict=True,
        ):
            with self.subTest(paragraph=item.number):
                episodes, _ = normalize_document(
                    complete_episode(
                        paragraph(3, "Richard： Start.开始。"),
                        item,
                    )
                )
                speakers = {
                    line.speaker for line in episodes[0].acts[0].lines
                }
                self.assertNotIn(false_speaker, speakers)
                self.assertIn(
                    item.number,
                    episodes[0].acts[0].lines[0].source_paragraphs,
                )

    def test_splits_real_double_speaker_paragraph(self):
        source = complete_episode(*real_paragraphs(3747))

        episodes, _ = normalize_document(source)

        lines = episodes[0].acts[0].lines
        self.assertEqual(
            [(line.speaker, line.english) for line in lines],
            [("Robbie", "Hi."), ("Carlson", "Hi.")],
        )
        self.assertEqual(
            [line.source_paragraphs for line in lines],
            [[3747], [3747]],
        )

    def test_real_document_smoke(self):
        episodes, issues = normalize_document(read_paragraphs(SOURCE_PATH))

        self.assertEqual(len(episodes), 26)
        self.assertTrue(
            all(
                [act.number for act in episode.acts] == [1, 2, 3]
                for episode in episodes
            )
        )
        all_lines = [
            line
            for episode in episodes
            for act in episode.acts
            for line in act.lines
        ]
        self.assertTrue(any(299 in line.source_paragraphs for line in all_lines))
        self.assertTrue(any(572 in line.source_paragraphs for line in all_lines))
        speakers = {line.speaker for line in all_lines}
        self.assertTrue({"Robbie", "Carlson"} <= speakers)
        self.assertTrue(
            speakers.isdisjoint({"salad", "Time", "Let's see. Name"})
        )
        self.assertTrue(
            any(
                issue.category == "inserted-act-boundary"
                and issue.episode == 3
                for issue in issues
            )
        )


if __name__ == "__main__":
    unittest.main()
