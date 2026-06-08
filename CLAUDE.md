# Family Album U.S.A. Project Rules

## Purpose

Build a responsive static bilingual reading site from the source DOCX. The site
is optimized for immersive reading and is published to GitHub Pages at
`usa.adihuang.com`.

## Project Structure

- `source/`: immutable source documents.
- `scripts/`: deterministic content extraction, cleanup, and site generation.
- `data/`: generated structured content and cleanup reports.
- `templates/`: static HTML templates.
- `assets/`: shared CSS and JavaScript source files.
- `docs/`: GitHub Pages root; generated site files live at the root and in
  `docs/assets/`, while `docs/superpowers/` contains authored specifications
  and plans.
- `tests/`: content, link, and generated HTML validation.
- `docs/superpowers/specs/`: approved design specifications.

## Naming

- Use lowercase `snake_case` for Python files and functions.
- Use lowercase `kebab-case` for generated HTML and asset filenames.
- Use English identifiers and English code comments.
- Generated episode pages use `episode-01.html` through `episode-26.html`.

## Source And Generated Files

- Do not edit the source DOCX during extraction or cleanup.
- Content corrections must be deterministic and documented in the cleanup
  report.
- Do not manually edit generated site files in the `docs/` root,
  `docs/assets/`, or generated files in `data/`.
- Files under `docs/superpowers/` are authored project documentation and must
  never be removed by site generation.
- Rebuild generated output after changing scripts, templates, or assets.

## Content Rules

- Preserve meaning. Do not rewrite or retranslate dialogue.
- Repair structural line breaks and only correct unambiguous spelling, name,
  punctuation, and spacing errors.
- Preserve uncertain source text and include it in the cleanup report.
- The expected structure is 26 episodes with 3 acts per episode.

## Web Rules

- Use static HTML, CSS, and minimal progressive-enhancement JavaScript.
- The full bilingual content must remain readable without JavaScript.
- Desktop dialogue uses English and Chinese columns.
- Mobile dialogue stacks the Chinese translation beneath its English line.
- Store only the Chinese visibility preference in `localStorage`.
- Do not add search, accounts, analytics, or reading-progress tracking.

## Validation

Before considering a change complete:

1. Run the content parser and static-site generator.
2. Run all automated tests.
3. Validate generated internal links and required HTML structure.
4. Check representative mobile and desktop pages in a browser.

Document exact commands in the implementation plan once the toolchain exists.

## Git

- Commit messages must be one short English sentence.
- Do not commit `.superpowers/` or temporary render artifacts.
- Do not push without explicit user approval.
