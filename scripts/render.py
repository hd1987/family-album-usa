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
    chinese = escape(line.chinese) if line.chinese else ""
    return (
        '<article class="dialogue-line">'
        '<div class="english-column">'
        f'<p class="speaker">{escape(line.speaker)}</p>'
        f'<p class="dialogue-text">{escape(line.english)}</p>'
        "</div>"
        '<div class="chinese-column" data-chinese-text>'
        '<p class="language-label">中文</p>'
        f'<p class="dialogue-text">{chinese}</p>'
        "</div>"
        "</article>"
    )


def render_index_page(episodes: list[Episode]) -> str:
    cards = "".join(
        '<a class="episode-card" '
        f'href="{_episode_filename(episode.number)}">'
        f'<span class="episode-number">{episode.number:02d}</span>'
        f"<strong>{escape(episode.english_title)}</strong>"
        f'<span data-chinese-text>{escape(episode.chinese_title)}</span>'
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
