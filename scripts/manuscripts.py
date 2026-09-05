"""Read manuscripts without changing their text or established section anchors."""
from __future__ import annotations
from dataclasses import dataclass
from html import escape
from pathlib import Path
import re

INLINE_CODE_PATTERN = re.compile(r"(`[^`]+`)")
ORDERED_LIST_PATTERN = re.compile(r"^\d+\.\s+")
FRONT_MATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.DOTALL)
SERIAL_TITLE_PATTERN = re.compile(r"^(.+?)（(前編|中編|後編)）$")

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
    series: str = ""
    episode: int | None = None


@dataclass
class IndexEntry:
    slug: str
    title: str
    excerpt: str
    sequence_label: str
    character_count: int
    reading_minutes: int
    part_count: int = 1
    latest_slug: str | None = None
    series_kind: str = ""
    latest_episode: int | None = None


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


def story_to_index_entry(story: Story) -> IndexEntry:
    return IndexEntry(
        slug=story.slug,
        title=story.title,
        excerpt=story.excerpt,
        sequence_label=story.sequence_label,
        character_count=story.character_count,
        reading_minutes=story.reading_minutes,
        latest_slug=story.slug,
    )


def make_index_entries(stories: list[Story]) -> list[IndexEntry]:
    entries: list[IndexEntry] = []
    index = 0
    part_order = {"前編": 0, "中編": 1, "後編": 2}

    while index < len(stories):
        story = stories[index]

        if story.series and story.episode is not None:
            group = [story]
            next_index = index + 1
            expected_episode = story.episode + 1
            while next_index < len(stories):
                next_story = stories[next_index]
                if next_story.series != story.series or next_story.episode != expected_episode:
                    break
                group.append(next_story)
                next_index += 1
                expected_episode += 1

            latest_story = group[-1]
            sequence_label = story.sequence_label
            if len(group) > 1:
                sequence_label = f"{story.sequence_label}-{latest_story.sequence_label}"
            entries.append(
                IndexEntry(
                    slug=story.slug,
                    title=story.series,
                    excerpt=latest_story.excerpt,
                    sequence_label=sequence_label,
                    character_count=sum(part.character_count for part in group),
                    reading_minutes=sum(part.reading_minutes for part in group),
                    part_count=len(group),
                    latest_slug=latest_story.slug,
                    series_kind="episode",
                    latest_episode=latest_story.episode,
                )
            )
            index = next_index
            continue

        title_match = SERIAL_TITLE_PATTERN.match(story.title)
        if not title_match:
            entries.append(story_to_index_entry(story))
            index += 1
            continue

        series_title, part_label = title_match.groups()
        group = [story]
        next_index = index + 1
        expected_order = part_order[part_label] + 1
        while next_index < len(stories):
            next_match = SERIAL_TITLE_PATTERN.match(stories[next_index].title)
            if not next_match:
                break
            next_title, next_part_label = next_match.groups()
            if next_title != series_title or part_order[next_part_label] != expected_order:
                break
            group.append(stories[next_index])
            next_index += 1
            expected_order += 1

        if len(group) == 1:
            entries.append(story_to_index_entry(story))
            index += 1
            continue

        excerpt = re.sub(r"^[一二三四五六七八九十]+\s+", "", group[0].excerpt)
        entries.append(
            IndexEntry(
                slug=group[0].slug,
                title=series_title,
                excerpt=excerpt,
                sequence_label=f"{group[0].sequence_label}-{group[-1].sequence_label}",
                character_count=sum(part.character_count for part in group),
                reading_minutes=sum(part.reading_minutes for part in group),
                part_count=len(group),
                latest_slug=group[0].slug,
                series_kind="parts",
            )
        )
        index = next_index

    return entries


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



def load_story(path: Path) -> Story:
    raw_text = path.read_text(encoding="utf-8")
    metadata, body_text = parse_front_matter(raw_text)
    fallback_title = metadata.get("title", path.stem)
    title, sections, html_body, plain_text = parse_markdown(body_text, fallback_title)

    description = metadata.get("description", make_excerpt(plain_text, limit=140))
    excerpt = metadata.get("excerpt", make_excerpt(plain_text))
    character_count = len(re.sub(r"\s+", "", plain_text))
    episode = None
    if metadata.get("episode"):
        try:
            episode = int(metadata["episode"])
        except ValueError as exc:
            raise ValueError(f"Invalid episode number in {path}: {metadata['episode']}") from exc

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
        series=metadata.get("series", ""),
        episode=episode,
    )
