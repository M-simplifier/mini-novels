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
SITE_SUBTITLE = "短編小説のための小さな読書室。"

INLINE_CODE_PATTERN = re.compile(r"(`[^`]+`)")
ORDERED_LIST_PATTERN = re.compile(r"^\d+\.\s+")
FRONT_MATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.DOTALL)

STYLE_CSS = """\
@import url("https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700&family=Noto+Serif+JP:wght@400;600;700;900&display=swap");

:root {
  --page: #f4f5f2;
  --surface: #fbfbf7;
  --surface-soft: #eef0eb;
  --ink: #191d20;
  --ink-soft: #343a3d;
  --muted: #6f7572;
  --rule: #c7cec4;
  --rule-strong: #90998f;
  --accent: #8b2635;
  --accent-deep: #561821;
  --teal: #26615c;
  --focus: #134fbd;
  --shadow: 0 18px 54px rgba(25, 29, 32, 0.08);
  --measure: 42rem;
  --shell: 1180px;
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
    linear-gradient(90deg, rgba(25, 29, 32, 0.035) 1px, transparent 1px),
    linear-gradient(180deg, rgba(25, 29, 32, 0.025) 1px, transparent 1px),
    linear-gradient(180deg, #fbfbf7 0%, var(--page) 42%, #e7ebe5 100%);
  background-size: 72px 72px, 100% 34px, auto;
  font-family:
    "Noto Serif JP",
    "BIZ UDPMincho",
    "Hiragino Mincho ProN",
    "Yu Mincho",
    serif;
  line-height: 1.9;
  text-rendering: optimizeLegibility;
}

a {
  color: inherit;
  text-decoration: none;
}

a:hover {
  color: var(--accent);
}

a:focus-visible,
button:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 4px;
}

.skip-link {
  position: fixed;
  top: 14px;
  left: 14px;
  z-index: 20;
  transform: translateY(-160%);
  padding: 9px 13px;
  background: var(--ink);
  color: var(--surface);
  font-family:
    "Avenir Next",
    "Noto Sans JP",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
  font-size: 0.85rem;
}

.skip-link:focus {
  transform: translateY(0);
}

.site-shell {
  width: min(var(--shell), calc(100vw - 44px));
  margin: 0 auto;
  padding: 26px 0 82px;
}

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 44px;
  border-bottom: 1px solid var(--rule);
  font-family:
    "Avenir Next",
    "Noto Sans JP",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
}

.brand {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  color: var(--ink);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.site-mark {
  color: var(--muted);
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.home-layout {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(360px, 1.08fr);
  gap: clamp(28px, 6vw, 78px);
  align-items: stretch;
  padding: clamp(42px, 8vw, 92px) 0 clamp(36px, 7vw, 78px);
  border-bottom: 1px solid var(--rule);
}

.home-intro {
  display: flex;
  min-height: 360px;
  flex-direction: column;
  justify-content: space-between;
}

.kicker,
.story-number,
.row-number,
.meta-chip,
.site-stat,
.story-label,
.story-toc h2,
.nav-link {
  font-family:
    "Avenir Next",
    "Noto Sans JP",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
}

.kicker {
  margin: 0;
  color: var(--accent);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.home-title {
  max-width: 8em;
  margin: 18px 0 0;
  font-size: clamp(4rem, 12vw, 9.5rem);
  font-weight: 700;
  letter-spacing: 0;
  line-height: 0.88;
}

.home-copy {
  max-width: 30rem;
  margin: 24px 0 0;
  color: var(--ink-soft);
  font-size: clamp(1.06rem, 0.5vw + 1rem, 1.28rem);
}

.collection-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, max-content));
  gap: 18px 34px;
  margin: 38px 0 0;
}

.collection-meta div {
  min-width: 0;
}

.collection-meta dt {
  color: var(--muted);
  font-family:
    "Avenir Next",
    "Noto Sans JP",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.collection-meta dd {
  margin: 5px 0 0;
  color: var(--ink);
  font-size: 1.25rem;
  line-height: 1.25;
}

.latest-panel {
  position: relative;
  display: flex;
  min-height: 360px;
  flex-direction: column;
  justify-content: space-between;
  padding: clamp(26px, 4vw, 44px);
  overflow: hidden;
  border: 1px solid var(--rule-strong);
  background:
    linear-gradient(135deg, rgba(139, 38, 53, 0.08), transparent 38%),
    var(--surface);
  box-shadow: var(--shadow);
}

.latest-panel::before {
  content: "";
  position: absolute;
  inset: 16px;
  pointer-events: none;
  border: 1px solid rgba(144, 153, 143, 0.42);
}

.latest-panel:hover {
  color: var(--ink);
  border-color: var(--accent);
}

.latest-panel:hover .latest-title {
  color: var(--accent-deep);
}

.latest-top {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 22px;
}

.story-number {
  color: var(--teal);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.latest-title {
  display: block;
  max-width: 11em;
  margin: 72px 0 0;
  font-size: clamp(2rem, 5vw, 4.3rem);
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.08;
  transition: color 180ms ease;
}

.latest-excerpt {
  display: block;
  max-width: 36rem;
  margin: 22px 0 0;
  color: var(--ink-soft);
  font-size: 1.03rem;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 22px;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 3px 9px;
  border: 1px solid var(--rule);
  color: var(--muted);
  background: rgba(251, 251, 247, 0.72);
  font-size: 0.76rem;
  line-height: 1.3;
}

.catalog {
  padding-top: clamp(36px, 6vw, 72px);
}

.section-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) max-content;
  gap: 20px;
  align-items: end;
  margin-bottom: 18px;
}

.section-heading h2 {
  margin: 8px 0 0;
  font-size: clamp(1.65rem, 3vw, 2.8rem);
  line-height: 1.15;
}

.site-stat {
  color: var(--muted);
  font-size: 0.82rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.story-list {
  margin: 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--ink);
}

.story-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) minmax(112px, max-content);
  gap: 22px;
  align-items: baseline;
  padding: 21px 0 23px;
  border-bottom: 1px solid var(--rule);
}

.story-row:hover {
  color: var(--ink);
}

.story-row:hover .row-title {
  color: var(--accent-deep);
}

.row-number {
  color: var(--teal);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.row-title {
  display: block;
  font-size: clamp(1.24rem, 1.2vw + 1rem, 1.75rem);
  font-weight: 700;
  line-height: 1.35;
}

.row-excerpt {
  display: block;
  max-width: 62rem;
  margin-top: 6px;
  color: var(--muted);
  font-size: 0.94rem;
  line-height: 1.75;
}

.row-meta {
  color: var(--muted);
  font-family:
    "Avenir Next",
    "Noto Sans JP",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.empty-state {
  padding: 32px 0;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule);
  color: var(--muted);
}

.reader-shell {
  display: grid;
  grid-template-columns: minmax(180px, 240px) minmax(0, var(--measure));
  gap: clamp(32px, 7vw, 96px);
  justify-content: center;
  padding: clamp(42px, 7vw, 82px) 0 0;
}

.reader-rail {
  position: sticky;
  top: 28px;
  align-self: start;
  padding-top: 8px;
  color: var(--muted);
  font-family:
    "Avenir Next",
    "Noto Sans JP",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
  font-size: 0.82rem;
  line-height: 1.6;
}

.reader-rail::before {
  content: "";
  display: block;
  width: 42px;
  height: 2px;
  margin-bottom: 18px;
  background: var(--accent);
}

.story-label {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.rail-block {
  padding: 18px 0;
  border-bottom: 1px solid var(--rule);
}

.rail-block:first-of-type {
  border-top: 1px solid var(--rule);
}

.rail-block p {
  margin: 0;
}

.story-toc {
  margin-top: 18px;
}

.story-toc h2 {
  margin: 0 0 10px;
  color: var(--accent);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.story-toc ol {
  margin: 0;
  padding-left: 1.1em;
}

.story-toc li + li {
  margin-top: 0.52em;
}

.story-toc a {
  color: var(--muted);
}

.story-toc a:hover {
  color: var(--accent);
}

.reader-main {
  min-width: 0;
}

.story-head {
  padding-bottom: 24px;
  border-bottom: 1px solid var(--ink);
}

.story-title {
  max-width: 13em;
  margin: 16px 0 0;
  font-size: clamp(2.25rem, 5.3vw, 5rem);
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.08;
}

.story-intro {
  margin: 20px 0 0;
  color: var(--ink-soft);
  font-size: clamp(1rem, 0.35vw + 0.98rem, 1.15rem);
  line-height: 1.9;
}

.story-body {
  margin-top: clamp(34px, 5vw, 56px);
  font-size: clamp(1.1rem, 0.55vw + 1rem, 1.24rem);
  letter-spacing: 0;
  line-height: 2.18;
}

.story-body h1 {
  display: none;
}

.story-body h2,
.story-body h3 {
  margin: 2.6em 0 1em;
  font-family:
    "Avenir Next",
    "Noto Sans JP",
    "Hiragino Sans",
    "Yu Gothic",
    sans-serif;
  letter-spacing: 0;
  line-height: 1.5;
}

.story-body h2 {
  font-size: 1.22em;
}

.story-body h3 {
  color: var(--muted);
  font-size: 1.08em;
}

.story-body p,
.story-body ul,
.story-body ol,
.story-body blockquote {
  margin: 0 0 1.18em;
}

.story-body ul,
.story-body ol {
  padding-left: 1.35em;
}

.story-body code {
  padding: 0.12em 0.34em;
  border: 1px solid rgba(38, 97, 92, 0.18);
  background: rgba(38, 97, 92, 0.06);
  color: var(--teal);
  font-size: 0.88em;
}

.story-body .display-code {
  text-align: center;
  margin: 1.5em 0;
}

.story-body .display-code code {
  display: inline-block;
  padding: 0.46em 0.84em;
  font-size: 0.92em;
}

.story-body blockquote {
  padding: 0.2em 0 0.2em 1.05em;
  border-left: 2px solid var(--accent);
  color: var(--ink-soft);
}

.footer-nav {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: clamp(38px, 6vw, 70px);
  padding-top: 18px;
  border-top: 1px solid var(--rule);
}

.nav-link {
  display: flex;
  min-height: 46px;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border: 1px solid var(--rule);
  background: rgba(251, 251, 247, 0.72);
  color: var(--ink-soft);
  font-size: 0.78rem;
  line-height: 1.35;
  text-align: center;
}

.nav-link:hover {
  border-color: var(--accent);
  color: var(--accent-deep);
}

@media (max-width: 900px) {
  .home-layout {
    grid-template-columns: 1fr;
  }

  .home-intro,
  .latest-panel {
    min-height: 0;
  }

  .latest-title {
    margin-top: 58px;
  }

  .reader-shell {
    grid-template-columns: 1fr;
    gap: 30px;
    max-width: var(--measure);
    margin: 0 auto;
  }

  .reader-rail {
    position: static;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0 18px;
    padding-top: 0;
  }

  .reader-rail::before {
    grid-column: 1 / -1;
  }

  .story-toc {
    grid-column: 1 / -1;
  }
}

@media (max-width: 680px) {
  .site-shell {
    width: min(100vw - 26px, var(--shell));
    padding-top: 18px;
  }

  .site-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 0;
    padding-bottom: 10px;
  }

  .site-mark {
    font-size: 0.72rem;
  }

  .home-layout {
    padding-top: 36px;
  }

  .home-title {
    font-size: clamp(3.5rem, 20vw, 5.8rem);
  }

  .collection-meta {
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .latest-panel {
    padding: 22px;
  }

  .latest-panel::before {
    inset: 10px;
  }

  .latest-title {
    margin-top: 42px;
  }

  .section-heading {
    grid-template-columns: 1fr;
  }

  .story-row {
    grid-template-columns: 52px minmax(0, 1fr);
    gap: 14px;
  }

  .row-meta {
    grid-column: 2;
  }

  .reader-shell {
    padding-top: 34px;
  }

  .reader-rail {
    grid-template-columns: 1fr;
  }

  .story-title {
    font-size: clamp(2.1rem, 13vw, 3.5rem);
  }

  .story-body {
    font-size: 1.08rem;
    line-height: 2.08;
  }

  .footer-nav {
    grid-template-columns: 1fr;
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
    sequence_label: str
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


def make_sequence_label(slug: str) -> str:
    match = re.match(r"^(\d+)", slug)
    return match.group(1) if match else slug


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
        latest_story = stories[-1]
        total_characters = sum(story.character_count for story in stories)
        total_minutes = sum(story.reading_minutes for story in stories)
        rows = "\n".join(
            f"""
            <li>
              <a class="story-row" href="stories/{story.slug}.html">
                <span class="row-number">{escape(story.sequence_label)}</span>
                <span class="row-main">
                  <span class="row-title">{escape(story.title)}</span>
                  <span class="row-excerpt">{escape(story.excerpt)}</span>
                </span>
                <span class="row-meta">{story.character_count}字 / 約{story.reading_minutes}分</span>
              </a>
            </li>
            """.strip()
            for story in reversed(stories)
        )
        body = f"""
        <section class="home-layout" aria-labelledby="home-title">
          <div class="home-intro">
            <div>
              <p class="kicker">Reading Room</p>
              <h1 class="home-title" id="home-title">{escape(SITE_TITLE)}</h1>
              <p class="home-copy">{escape(SITE_SUBTITLE)}</p>
            </div>
            <dl class="collection-meta">
              <div>
                <dt>Stories</dt>
                <dd>{len(stories)}</dd>
              </div>
              <div>
                <dt>Reading</dt>
                <dd>約{total_minutes}分</dd>
              </div>
              <div>
                <dt>Letters</dt>
                <dd>{total_characters}字</dd>
              </div>
            </dl>
          </div>
          <a class="latest-panel" href="stories/{latest_story.slug}.html">
            <span class="latest-top">
              <span class="kicker">Latest</span>
              <span class="story-number">{escape(latest_story.sequence_label)}</span>
            </span>
            <span>
              <span class="latest-title">{escape(latest_story.title)}</span>
              <span class="latest-excerpt">{escape(latest_story.excerpt)}</span>
            </span>
            <span class="meta-row">
              <span class="meta-chip">{latest_story.character_count}字</span>
              <span class="meta-chip">約{latest_story.reading_minutes}分</span>
            </span>
          </a>
        </section>
        <section class="catalog" aria-labelledby="catalog-title">
          <div class="section-heading">
            <div>
              <p class="kicker">Archive</p>
              <h2 id="catalog-title">作品目次</h2>
            </div>
            <div class="site-stat">{len(stories)} stories</div>
          </div>
          <ol class="story-list">
            {rows}
          </ol>
        </section>
        """.strip()
    else:
        body = '<section class="empty-state">`stories/` に Markdown を置くと、ここに一覧が出ます。</section>'

    return render_page(
        page_title="Home",
        stylesheet_path="assets/style.css",
        main_content=body,
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
        <div class="story-toc">
          <h2>Contents</h2>
          <ol>
            {toc_items}
          </ol>
        </div>
        """.strip()
    else:
        toc_html = ""
    toc_block = f"\n            {toc_html}" if toc_html else ""

    footer_links = ['<a class="nav-link" href="../index.html">目次へ戻る</a>']
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
        <article class="reader-shell">
          <aside class="reader-rail" aria-label="Story navigation">
            <div class="rail-block">
              <p class="story-label">Story</p>
              <p>{escape(story.sequence_label)}</p>
            </div>
            <div class="rail-block">
              <p class="story-label">Length</p>
              <p>{story.character_count}字 / 約{story.reading_minutes}分</p>
            </div>{toc_block}
          </aside>
          <div class="reader-main">
            <header class="story-head">
              <p class="story-number">{escape(story.sequence_label)}</p>
              <h1 class="story-title">{escape(story.title)}</h1>
              <p class="story-intro">{escape(story.description)}</p>
            </header>
            <div class="story-body">
              {story.html_body}
            </div>
            <nav class="footer-nav" aria-label="Story links">
              {"".join(footer_links)}
            </nav>
          </div>
        </article>
        """.strip(),
    )


def render_page(page_title: str, stylesheet_path: str, main_content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(page_title)} | {escape(SITE_TITLE)}</title>
    <link rel="icon" href="data:,">
    <link rel="stylesheet" href="{escape(stylesheet_path)}">
  </head>
  <body>
    <a class="skip-link" href="#main">本文へ</a>
    <div class="site-shell">
      <header class="site-header">
        <a class="brand" href="{('index.html' if stylesheet_path == 'assets/style.css' else '../index.html')}">{escape(SITE_TITLE)}</a>
        <span class="site-mark">Short Fiction</span>
      </header>
      <main id="main">
        {main_content}
      </main>
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
        sequence_label=make_sequence_label(path.stem),
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
