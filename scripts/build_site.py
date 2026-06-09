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
        identifier = values.get("id")
        if identifier:
            self.ids.append(identifier)
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
    assets_output = output_dir / "assets"
    assets_output.mkdir(exist_ok=True)

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


def _parse(path: Path) -> SiteParser:
    parser = SiteParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def _validate_target(
    output_dir: Path,
    source_page: Path,
    target: str,
) -> None:
    if target.startswith(("http://", "https://", "mailto:")):
        return

    path_part, _, fragment = target.partition("#")
    target_path = source_page if not path_part else output_dir / path_part
    if not target_path.exists():
        raise ValueError(
            f"Broken local target in {source_page.name}: {target}"
        )
    if fragment and target_path.suffix == ".html":
        if fragment not in _parse(target_path).ids:
            raise ValueError(
                f"Missing fragment in {source_page.name}: {target}"
            )


def validate_site(output_dir: Path) -> None:
    episode_pages = sorted(output_dir.glob("episode-*.html"))
    if len(episode_pages) != 26:
        raise ValueError("Expected exactly 26 generated episode pages")

    pages = [output_dir / "index.html", *episode_pages]
    for page in pages:
        parser = _parse(page)
        if len(parser.ids) != len(set(parser.ids)):
            raise ValueError(f"Duplicate HTML id in {page.name}")
        if page.name.startswith("episode-"):
            for act_id in ("act-1", "act-2", "act-3"):
                if act_id not in parser.ids:
                    raise ValueError(f"Missing {act_id} in {page.name}")
        for target in [*parser.links, *parser.sources]:
            _validate_target(output_dir, page, target)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("data_path", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_site(args.data_path, args.output_dir)


if __name__ == "__main__":
    main()
