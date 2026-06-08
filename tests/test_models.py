import unittest

from scripts.models import Act, Correction, DialogueLine, Episode


class ContentModelTest(unittest.TestCase):
    def test_episode_to_dict_serializes_nested_content(self):
        correction = Correction(
            category="spelling",
            before="helo",
            after="hello",
            confidence="high",
        )
        line = DialogueLine(
            speaker="Richard",
            english="Hello.",
            chinese="你好。",
            source_paragraphs=[12, 13],
            corrections=[correction],
        )
        episode = Episode(
            number=1,
            english_title="A Family Album",
            chinese_title="家庭相册",
            acts=[Act(number=1, lines=[line])],
        )

        self.assertEqual(
            episode.to_dict(),
            {
                "number": 1,
                "english_title": "A Family Album",
                "chinese_title": "家庭相册",
                "acts": [
                    {
                        "number": 1,
                        "lines": [
                            {
                                "speaker": "Richard",
                                "english": "Hello.",
                                "chinese": "你好。",
                                "source_paragraphs": [12, 13],
                                "corrections": [
                                    {
                                        "category": "spelling",
                                        "before": "helo",
                                        "after": "hello",
                                        "confidence": "high",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        )

    def test_act_rejects_invalid_number(self):
        with self.assertRaisesRegex(ValueError, "act number"):
            Act(number=0, lines=[])


if __name__ == "__main__":
    unittest.main()
