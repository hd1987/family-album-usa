# Static Bilingual Reader Design

## Goal

Convert `走遍美国中英文对照.docx` into a responsive static website for
immersive bilingual reading on phones and desktop computers.

The site will be published through GitHub Pages at `usa.adihuang.com`. It will
not be actively promoted, but anyone who knows the URL can access it. This is
not access control.

## Scope

### Included

- A directory page for all 26 episodes.
- One reading page per episode.
- Three acts displayed continuously on each episode page.
- English and Chinese side-by-side on desktop.
- Chinese stacked beneath the matching English line on mobile.
- A global Chinese visibility control.
- Browser-local persistence of the Chinese visibility preference.
- Previous and next episode navigation.
- Act anchor navigation within each episode.
- Deterministic cleanup of structural and unambiguous source errors.
- GitHub Pages output and the custom domain configuration file.

### Excluded

- Search.
- Accounts or authentication.
- Reading history or learning progress.
- Content management or editing interfaces.
- Audio, vocabulary notes, annotations, or exercises.
- Analytics.
- Password protection.
- Semantic rewriting or retranslation of source dialogue.

## Technical Approach

Use a custom static generation pipeline with Python, HTML, CSS, and minimal
JavaScript. No frontend framework or server runtime is required.

The build pipeline is:

```text
Source DOCX
  -> extract paragraphs and run metadata
  -> identify episodes, acts, speakers, English, and Chinese
  -> merge structural line breaks
  -> apply deterministic corrections
  -> validate structured content
  -> write data/episodes.json and a cleanup report
  -> render the directory and 26 episode pages
  -> validate links and generated HTML
```

The structured JSON is retained as an auditable intermediate artifact. The
deployed site contains only static files.

## Project Structure

```text
CLAUDE.md
source/
  走遍美国中英文对照.docx
scripts/
  build_content.py
  build_site.py
data/
  episodes.json
  cleanup-report.json
templates/
  index.html
  episode.html
assets/
  styles.css
  reader.js
docs/
  index.html
  episode-01.html
  ...
  episode-26.html
  assets/
  CNAME
  superpowers/
    specs/
    plans/
tests/
```

The original DOCX currently at the repository root will be moved to `source/`
during implementation. Moving the file requires explicit user approval because
project rules treat file removal or relocation as a protected operation.

The site generator owns only the generated files at the `docs/` root and
`docs/assets/`. It must preserve authored files under `docs/superpowers/`.

## Content Model

The normalized data contains:

```text
Episode
  number
  english_title
  chinese_title
  acts[]

Act
  number
  lines[]

DialogueLine
  speaker
  english
  chinese
  source_paragraphs[]
  corrections[]
```

`source_paragraphs` preserves traceability to the original document.
`corrections` records applied deterministic changes.

## Content Cleanup

### Automatic Structural Cleanup

- Remove the duplicate episode list and character-color legend before Episode 1.
- Normalize `Episode` and `Act` headings.
- Merge paragraphs split in the middle of a dialogue line.
- Detect speaker prefixes using the full-width colon and known variants.
- Separate English and Chinese text without changing their meaning.
- Normalize repeated spaces and obvious punctuation spacing.

### Allowed Corrections

- Unambiguous character-name variants such as obvious single-letter typos.
- Unambiguous English spelling mistakes.
- Consistent punctuation and spacing.
- Missing Act labels only when surrounding episode structure proves the act
  boundary.

### Uncertain Content

If a correction cannot be established confidently:

- Preserve the source text.
- Add an entry to `data/cleanup-report.json`.
- Do not infer a translation or rewrite dialogue.

The report includes the episode, act, speaker, source text, issue category,
applied correction when present, and confidence classification.

## Information Architecture

### Directory Page

The root page lists 26 episode cards. Each card shows:

- Episode number.
- English title.
- Chinese title when available.

The page includes a short description explaining that the site contains a
bilingual script and that Chinese can be hidden.

### Episode Page

Each episode page contains:

- A top navigation bar with a directory link and Chinese visibility control.
- Episode number and bilingual title.
- Act links for quick navigation.
- All three acts in continuous reading order.
- Previous and next episode links at the bottom.

The first episode omits the previous link. The last episode omits the next link.

## Responsive Reading Layout

### Desktop

- Use a constrained reading width to avoid long lines.
- Render each dialogue record as a two-column grid.
- Keep English on the left and Chinese on the right.
- Align translations by dialogue record rather than independent document
  columns, preventing drift when translations have different lengths.

### Mobile

- Collapse each dialogue record to one column.
- Place Chinese directly beneath its matching English line.
- Keep the speaker label visually attached to the dialogue pair.
- Use touch-friendly navigation and toggle controls.

## Chinese Visibility

The complete bilingual content remains in the HTML.

- First visit: Chinese is visible.
- Toggling Chinese adds or removes a document-level CSS state.
- Store the preference in `localStorage`.
- Apply the stored preference on later visits.
- If JavaScript is unavailable, Chinese remains visible and the site remains
  fully readable.

The site does not store the current episode, scroll position, or learning
progress.

## Visual System

Use a restrained paper-script direction:

- Warm off-white page background.
- Dark brown or charcoal body text.
- Muted rust accent for episode labels, speaker names, and controls.
- Readable serif typography for English dialogue.
- A system CJK font stack for Chinese text.
- Subtle rules and spacing instead of card-heavy decoration.
- Minimal shadows and animation.

The design should feel like a carefully typeset script, not an application
dashboard.

## Accessibility

- Use semantic headings and navigation landmarks.
- Use real buttons and links with visible keyboard focus.
- Expose the Chinese toggle state with `aria-pressed`.
- Maintain sufficient color contrast.
- Do not rely on color alone to identify speakers or controls.
- Respect reduced-motion preferences.
- Keep content readable at 200 percent zoom.

## Error Handling

The build must fail when:

- The episode count is not 26.
- An episode cannot be assigned three acts after deterministic normalization.
- A dialogue line has no speaker or English text.
- Duplicate episode numbers or output filenames exist.
- Generated internal links do not resolve.

Missing Chinese text does not fail the build, but it must appear in the cleanup
report.

## Testing

### Content Tests

- Exactly 26 episodes.
- Exactly 3 acts per episode.
- Episode numbers are sequential.
- Dialogue records have speakers and English text.
- Missing Chinese lines are reported.
- Applied corrections are present in the cleanup report.

### Generated Site Tests

- Directory links resolve to all 26 episode pages.
- Act anchors exist and are unique.
- Previous and next links are correct.
- Every page includes the Chinese toggle and shared assets.
- `docs/CNAME` contains only `usa.adihuang.com`.
- Generated HTML passes structural parsing without malformed nesting.

### Browser Verification

Inspect at least:

- A narrow mobile viewport.
- A common tablet or small laptop viewport.
- A wide desktop viewport.
- Chinese shown and hidden states.
- First, middle, and final episode navigation.
- JavaScript-disabled rendering.

## Deployment

Publish the `docs/` directory through GitHub Pages. Configure the custom
subdomain `usa.adihuang.com` with a DNS `CNAME` record pointing to the
repository owner's GitHub Pages hostname, then enable HTTPS enforcement after
GitHub provisions the certificate.

The repository visibility and GitHub account plan determine whether the source
repository can remain private. The website itself is treated as publicly
reachable by URL.

## Success Criteria

- The full source is represented as 26 browsable episode pages.
- Desktop and mobile layouts remain comfortable for long reading sessions.
- Chinese visibility works and persists without tracking reading progress.
- The site remains readable without JavaScript.
- Content corrections are deterministic and auditable.
- All automated validations pass.
- The generated output is ready for GitHub Pages at `usa.adihuang.com`.
