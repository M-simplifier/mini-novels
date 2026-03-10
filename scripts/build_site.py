#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = ROOT / "stories"
SITE_DIR = ROOT / "site"
SITE_STORIES_DIR = SITE_DIR / "stories"
SITE_ASSETS_DIR = SITE_DIR / "assets"

SITE_TITLE = "Mini Novels"
SITE_SUBTITLE = "短編小説を、読むための静的Webページとしてまとめています。"

INLINE_CODE_PATTERN = re.compile(r"(`[^`]+`)")
ORDERED_LIST_PATTERN = re.compile(r"^\d+\.\s+")
FRONT_MATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.DOTALL)

STYLE_CSS = """\
:root {
  --bg: #f7f1e4;
  --bg-accent: #e4ecdf;
  --paper: rgba(255, 252, 246, 0.88);
  --paper-strong: rgba(255, 252, 246, 0.95);
  --line: rgba(64, 53, 42, 0.12);
  --ink: #2b241e;
  --muted: #6d6155;
  --accent: #194c44;
  --accent-soft: rgba(25, 76, 68, 0.1);
  --shadow: 0 20px 60px rgba(74, 59, 41, 0.1);
  --radius: 24px;
  --content-width: 760px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.6), transparent 32%),
    radial-gradient(circle at bottom right, rgba(197, 217, 207, 0.35), transparent 26%),
    linear-gradient(180deg, var(--bg), #efe6d4 100%);
  font-family:
    "BIZ UDPMincho",
    "Hiragino Mincho ProN",
    "Yu Mincho",
    "Noto Serif JP",
    serif;
  line-height: 1.85;
}

a {
  color: var(--accent);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.site-shell {
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 32px 0 72px;
}

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 28px;
}

.brand {
  font-family:
    "Avenir Next",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
  font-size: 0.92rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
}

.hero,
.story-frame,
.story-card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  backdrop-filter: blur(12px);
}

.hero {
  padding: 32px;
  margin-bottom: 28px;
}

.hero h1,
.story-title {
  margin: 0;
  font-weight: 700;
  line-height: 1.25;
  font-size: clamp(2rem, 4vw, 3.4rem);
}

.hero p {
  margin: 14px 0 0;
  max-width: 56rem;
  color: var(--muted);
  font-size: 1.02rem;
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
}

.story-card {
  display: block;
  padding: 24px;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

.story-card:hover {
  transform: translateY(-3px);
  text-decoration: none;
  border-color: rgba(25, 76, 68, 0.25);
  box-shadow: 0 24px 70px rgba(74, 59, 41, 0.15);
}

.story-card h2 {
  margin: 0 0 12px;
  font-size: 1.45rem;
  line-height: 1.35;
}

.story-card p {
  margin: 0;
  color: var(--muted);
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  padding: 7px 12px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-family:
    "Avenir Next",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
  font-size: 0.84rem;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.story-frame {
  padding: 28px;
}

.story-layout {
  display: grid;
  grid-template-columns: minmax(0, var(--content-width)) minmax(220px, 280px);
  gap: 28px;
  align-items: start;
}

.story-main {
  min-width: 0;
}

.story-intro {
  color: var(--muted);
  margin: 14px 0 0;
  font-size: 1rem;
}

.story-body {
  margin-top: 28px;
  font-size: clamp(1.08rem, 1.3vw + 0.85rem, 1.28rem);
  line-height: 2.1;
}

.story-body h1 {
  display: none;
}

.story-body h2,
.story-body h3 {
  margin: 2.5em 0 0.9em;
  line-height: 1.45;
  font-family:
    "Avenir Next",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
}

.story-body h2 {
  font-size: 1.28em;
}

.story-body h3 {
  font-size: 1.12em;
  color: var(--muted);
}

.story-body p,
.story-body ul,
.story-body ol,
.story-body blockquote {
  margin: 0 0 1.15em;
}

.story-body ul,
.story-body ol {
  padding-left: 1.5em;
}

.story-body code {
  padding: 0.15em 0.38em;
  border-radius: 0.4em;
  background: rgba(22, 61, 56, 0.08);
  font-size: 0.92em;
  color: var(--accent);
}

.story-body .display-code {
  text-align: center;
  margin: 1.4em 0;
}

.story-body .display-code code {
  display: inline-block;
  padding: 0.45em 0.9em;
  font-size: 0.95em;
}

.story-body blockquote {
  padding-left: 1em;
  border-left: 3px solid rgba(25, 76, 68, 0.22);
  color: var(--muted);
}

.story-toc {
  position: sticky;
  top: 24px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: var(--paper-strong);
}

.story-toc h2 {
  margin: 0 0 10px;
  font-size: 0.95rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  font-family:
    "Avenir Next",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
}

.story-toc ol {
  margin: 0;
  padding-left: 1.2em;
}

.story-toc li + li {
  margin-top: 0.5em;
}

.footer-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.nav-link {
  padding: 11px 15px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--paper-strong);
}

.empty-state {
  padding: 28px;
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  color: var(--muted);
}

@media (max-width: 980px) {
  .story-layout {
    grid-template-columns: 1fr;
  }

  .story-toc {
    position: static;
  }
}

@media (max-width: 640px) {
  .site-shell {
    width: min(100vw - 20px, 1180px);
    padding-top: 20px;
  }

  .hero,
  .story-frame {
    padding: 22px;
  }

  .story-card {
    padding: 20px;
  }
}
"""


@dataclass
class Section:
    id: str
    title: str


@dataclass
class Story:
    slug: str
    title: str
    description: str
    excerpt: str
    source_name: str
    html_body: str
    sections: list[Section]
    character_count: int
    reading_minutes: int


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    match = FRONT_MATTER_PATTERN.match(text)
    if not match:
        return {}, text

    raw_meta, body = match.groups()
    metadata: dict[str, str] = {}
    for line in raw_meta.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata, body


def render_inline(text: str) -> str:
    parts = INLINE_CODE_PATTERN.split(text)
    rendered: list[str] = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            rendered.append(f"<code>{escape(part[1:-1])}</code>")
        else:
            rendered.append(escape(part))
    return "".join(rendered)


def is_display_code(lines: list[str]) -> bool:
    return bool(lines) and all(
        line.strip().startswith("`") and line.strip().endswith("`")
        for line in lines
    )


def make_excerpt(text: str, limit: int = 110) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def estimate_reading_minutes(character_count: int) -> int:
    return max(1, round(character_count / 700))


def parse_markdown(text: str, fallback_title: str) -> tuple[str, list[Section], str, str]:
    blocks: list[str] = []
    sections: list[Section] = []
    plain_parts: list[str] = []
    paragraph_lines: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []
    title = fallback_title
    heading_index = 0

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return

        rendered_lines = [render_inline(line) for line in paragraph_lines]
        joined_text = "<br>\n".join(rendered_lines)
        if is_display_code(paragraph_lines):
            blocks.append(f'<p class="display-code">{joined_text}</p>')
        else:
            blocks.append(f"<p>{joined_text}</p>")
        plain_parts.append("\n".join(paragraph_lines))
        paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_kind, list_items
        if not list_kind or not list_items:
            list_kind = None
            list_items = []
            return

        tag = "ul" if list_kind == "ul" else "ol"
        items_html = "\n".join(f"<li>{item}</li>" for item in list_items)
        blocks.append(f"<{tag}>\n{items_html}\n</{tag}>")
        plain_parts.extend(list_items)
        list_kind = None
        list_items = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            flush_list()

            level = len(stripped) - len(stripped.lstrip("#"))
            heading_text = stripped[level:].strip()
            if not heading_text:
                continue

            if level == 1:
                title = heading_text
            else:
                heading_index += 1
                heading_id = f"section-{heading_index}"
                if level == 2:
                    sections.append(Section(id=heading_id, title=heading_text))
                blocks.append(f'<h{level} id="{heading_id}">{render_inline(heading_text)}</h{level}>')
                plain_parts.append(heading_text)
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            flush_list()
            quote_text = stripped[2:].strip()
            blocks.append(f"<blockquote>{render_inline(quote_text)}</blockquote>")
            plain_parts.append(quote_text)
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_paragraph()
            item_text = stripped[2:].strip()
            if list_kind not in (None, "ul"):
                flush_list()
            list_kind = "ul"
            list_items.append(render_inline(item_text))
            continue

        if ORDERED_LIST_PATTERN.match(stripped):
            flush_paragraph()
            item_text = ORDERED_LIST_PATTERN.sub("", stripped, count=1).strip()
            if list_kind not in (None, "ol"):
                flush_list()
            list_kind = "ol"
            list_items.append(render_inline(item_text))
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    flush_list()

    html_body = "\n".join(blocks)
    plain_text = "\n".join(plain_parts).strip()
    return title, sections, html_body, plain_text


def render_index_page(stories: list[Story]) -> str:
    if stories:
        cards = "\n".join(
            f"""
            <a class="story-card" href="stories/{story.slug}.html">
              <h2>{escape(story.title)}</h2>
              <p>{escape(story.excerpt)}</p>
              <div class="meta-row">
                <span class="meta-chip">{story.character_count}字</span>
                <span class="meta-chip">約{story.reading_minutes}分</span>
              </div>
            </a>
            """.strip()
            for story in stories
        )
        body = f'<section class="story-grid">\n{cards}\n</section>'
    else:
        body = '<section class="empty-state">`stories/` に Markdown を置くと、ここに一覧が出ます。</section>'

    return render_page(
        page_title="Home",
        stylesheet_path="assets/style.css",
        main_content=f"""
        <section class="hero">
          <div class="brand">Reading Workspace</div>
          <h1>{escape(SITE_TITLE)}</h1>
          <p>{escape(SITE_SUBTITLE)}</p>
        </section>
        {body}
        """.strip(),
    )


def render_story_page(stories: list[Story], index: int) -> str:
    story = stories[index]
    previous_story = stories[index - 1] if index > 0 else None
    next_story = stories[index + 1] if index < len(stories) - 1 else None

    if story.sections:
        toc_items = "\n".join(
            f'<li><a href="#{section.id}">{escape(section.title)}</a></li>'
            for section in story.sections
        )
        toc_html = f"""
        <aside class="story-toc">
          <h2>Contents</h2>
          <ol>
            {toc_items}
          </ol>
        </aside>
        """.strip()
    else:
        toc_html = ""

    footer_links = ['<a class="nav-link" href="../index.html">一覧へ戻る</a>']
    if previous_story:
        footer_links.append(
            f'<a class="nav-link" href="{previous_story.slug}.html">前の話: {escape(previous_story.title)}</a>'
        )
    if next_story:
        footer_links.append(
            f'<a class="nav-link" href="{next_story.slug}.html">次の話: {escape(next_story.title)}</a>'
        )

    return render_page(
        page_title=story.title,
        stylesheet_path="../assets/style.css",
        main_content=f"""
        <section class="story-frame">
          <div class="story-layout">
            <div class="story-main">
              <h1 class="story-title">{escape(story.title)}</h1>
              <p class="story-intro">{escape(story.description)}</p>
              <div class="meta-row">
                <span class="meta-chip">{story.character_count}字</span>
                <span class="meta-chip">約{story.reading_minutes}分</span>
              </div>
              <article class="story-body">
                {story.html_body}
              </article>
              <nav class="footer-nav">
                {"".join(footer_links)}
              </nav>
            </div>
            {toc_html}
          </div>
        </section>
        """.strip(),
    )


def render_page(page_title: str, stylesheet_path: str, main_content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(page_title)} | {escape(SITE_TITLE)}</title>
    <link rel="stylesheet" href="{escape(stylesheet_path)}">
  </head>
  <body>
    <div class="site-shell">
      <header class="site-header">
        <a class="brand" href="{('index.html' if stylesheet_path == 'assets/style.css' else '../index.html')}">{escape(SITE_TITLE)}</a>
      </header>
      {main_content}
    </div>
  </body>
</html>
"""


def load_story(path: Path) -> Story:
    raw_text = path.read_text(encoding="utf-8")
    metadata, body_text = parse_front_matter(raw_text)
    fallback_title = metadata.get("title", path.stem)
    title, sections, html_body, plain_text = parse_markdown(body_text, fallback_title)

    description = metadata.get("description", make_excerpt(plain_text, limit=140))
    excerpt = metadata.get("excerpt", make_excerpt(plain_text))
    character_count = len(re.sub(r"\s+", "", plain_text))

    return Story(
        slug=path.stem,
        title=title,
        description=description,
        excerpt=excerpt,
        source_name=path.name,
        html_body=html_body,
        sections=sections,
        character_count=character_count,
        reading_minutes=estimate_reading_minutes(character_count),
    )


def ensure_output_dirs() -> None:
    SITE_DIR.mkdir(exist_ok=True)
    SITE_STORIES_DIR.mkdir(exist_ok=True)
    SITE_ASSETS_DIR.mkdir(exist_ok=True)


def clear_generated_story_pages() -> None:
    for path in SITE_STORIES_DIR.glob("*.html"):
        path.unlink()


def build_site() -> None:
    ensure_output_dirs()
    clear_generated_story_pages()

    story_paths = sorted(STORIES_DIR.glob("*.md"))
    stories = [load_story(path) for path in story_paths]

    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (SITE_ASSETS_DIR / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (SITE_DIR / "index.html").write_text(render_index_page(stories), encoding="utf-8")

    for index, story in enumerate(stories):
        output_path = SITE_STORIES_DIR / f"{story.slug}.html"
        output_path.write_text(render_story_page(stories, index), encoding="utf-8")

    print(f"Built {len(stories)} stories into {SITE_DIR}")


if __name__ == "__main__":
    build_site()
