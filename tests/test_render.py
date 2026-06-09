from pathlib import Path
import unittest

from scripts.models import Act, DialogueLine, Episode
from scripts.render import render_episode_page, render_index_page


ROOT = Path(__file__).resolve().parents[1]
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
        self.assertIn("一本摄影集。", html)
        self.assertIn("data-chinese-text", html)
        self.assertNotIn('class="previous-episode"', html)
        self.assertNotIn("{{", html)

    def test_episode_renders_previous_and_next_navigation(self):
        previous = Episode(0, "Previous", "上一集", EPISODE.acts)
        following = Episode(2, "Following", "下一集", EPISODE.acts)

        html = render_episode_page(EPISODE, previous, following)

        self.assertIn('href="episode-00.html"', html)
        self.assertIn('href="episode-02.html"', html)

    def test_templates_load_shared_assets_and_module(self):
        html = render_episode_page(EPISODE, previous=None, following=None)

        self.assertIn('href="assets/styles.css"', html)
        self.assertIn(
            '<script type="module" src="assets/reader.js"></script>',
            html,
        )

    def test_stylesheet_contains_required_responsive_contract(self):
        css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")

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
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)


if __name__ == "__main__":
    unittest.main()
