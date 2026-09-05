#!/usr/bin/env python3
"""Build the reading room with only Python's standard library."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html import escape as e
import importlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))
import manuscripts

SITE = ROOT / 'site'
PUBLIC_URL = 'https://m-simplifier.github.io/mini-novels/'
DESCRIPTION = 'Mini Novelsは、短編小説と連載小説を読める小さな作品集です。'
ASSET_VERSION = ''
READING_INDEX = {}


@dataclass
class Work:
    slug: str
    title: str
    description: str
    genre: str
    stories: list
    ongoing: bool

    @property
    def serial(self):
        return len(self.stories) > 1 or self.ongoing

    @property
    def href(self):
        return f'works/{self.slug}.html' if self.serial else f'stories/{self.stories[0].slug}.html'

    @property
    def minutes(self):
        return sum(s.reading_minutes for s in self.stories)

    @property
    def status(self):
        if self.ongoing:
            return f'連載中 · {len(self.stories)}話まで公開'
        return f'完結 · 全{len(self.stories)}編' if self.serial else '短編'


def collect_works(stories):
    catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
    by_slug = {s.slug: s for s in stories}
    works = []
    for entry in manuscripts.make_index_entries(stories):
        first = by_slug[entry.slug]
        start = stories.index(first)
        editorial = catalog.get(first.slug, {})
        works.append(Work(editorial.get('slug', first.slug), entry.title,
                          editorial.get('description', first.description),
                          editorial.get('genre', '小説'), stories[start:start + entry.part_count],
                          entry.series_kind == 'episode'))
    return works


def arrow():
    return '<span aria-hidden="true">↗</span>'


def chapter_title(story):
    if story.series:
        return story.title.removeprefix(story.series).strip()
    match = manuscripts.SERIAL_TITLE_PATTERN.match(story.title)
    return match.group(2) if match else story.title


def cover_title(title):
    main, separator, sub = title.partition('――')
    return e(main) + (f'<span class="title-sub">{e(sub)}</span>' if separator else '')


def continue_slot(prefix, work=''):
    index = json.dumps(READING_INDEX, ensure_ascii=False).replace('<', '\\u003c')
    return f'''<aside class="continue-slot" data-continue data-prefix="{prefix}" data-work-id="{e(work)}" hidden aria-label="前回の続き">
      <span class="eyebrow">読みかけの一冊</span><a class="continue-link" href="{prefix}index.html"></a>
      <span class="continue-note"></span></aside><script id="reading-index" type="application/json">{index}</script>'''


def page(title, body, path, *, description=DESCRIPTION, reader=False):
    prefix = '../' * (len(Path(path).parts) - 1)
    canonical = PUBLIC_URL + path
    full_title = 'Mini Novels — 小説を読む' if path == 'index.html' else f'{title} | Mini Novels'
    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
{'<base href="' + PUBLIC_URL + '">' if path == '404.html' else ''}
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{e(full_title)}</title>
  <meta name="description" content="{e(description)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="{'article' if reader else 'website'}">
  <meta property="og:title" content="{e(title if path != 'index.html' else 'Mini Novels')}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Mini Novels">
  <meta property="og:locale" content="ja_JP">
  <link rel="icon" type="image/svg+xml" href="{prefix}assets/favicon.svg">
  <script src="{prefix}assets/theme.js?v={ASSET_VERSION}"></script>
  <link rel="stylesheet" href="{prefix}assets/style.css?v={ASSET_VERSION}">
  <script defer src="{prefix}assets/reader.js?v={ASSET_VERSION}"></script>
</head>
<body class="{'reading-page' if reader else 'collection-page'}" data-root="{prefix}">
  <a class="skip-link" href="#main">本文へ移動</a>
  <header class="site-header shell">
    <a class="brand" href="{prefix}index.html" aria-label="Mini Novels ホーム">mini novels<span class="brand-dot" aria-hidden="true">.</span></a>
    <nav aria-label="サイト内の移動"><a href="{prefix}index.html#library">作品一覧</a><a href="{prefix}about.html">この場所について</a></nav>
  </header>
  <main id="main" tabindex="-1">{body}</main>
  <footer class="site-footer shell"><a class="footer-brand" href="{prefix}index.html">Mini Novels</a>
    <div><a href="{prefix}archive/index.html">初期版アーカイブ</a><a href="{prefix}about.html">この場所について</a><a href="#main">ページの先頭へ ↑</a></div>
  </footer>
</body>
</html>
'''


def work_row(work, number, prefix=''):
    return f'''<li class="work-row" data-work data-search="{e(work.title + ' ' + work.description + ' ' + work.genre)}" data-kind="{'serial' if work.serial else 'short'}">
      <span class="work-number" aria-hidden="true">{number:02d}</span>
      <div class="work-detail"><div class="work-meta"><span>{e(work.genre)}</span><span>{e(work.status)}</span></div>
      <h3><a href="{prefix}{work.href}">{e(work.title)} {arrow()}</a></h3>
      <p>{e(work.description)}</p></div><span class="work-duration">約{work.minutes}分{'<small>公開分を通して</small>' if work.ongoing else ''}</span></li>'''


def opening_quote(story):
    paragraphs = re.findall(r'<p(?: [^>]*)?>(.*?)</p>', story.html_body, re.S)
    return '<p>' + '</p><p>'.join(paragraphs[:2]) + '</p>'


def home(works):
    featured = works[-1] if works else None
    if not featured:
        return page('Mini Novels', '<div class="shell page-intro"><h1>Mini Novels</h1><p>作品の公開を準備しています。</p></div>', 'index.html')
    first, latest = featured.stories[0], featured.stories[-1]
    short_count = sum(not w.serial for w in works)
    rows = '\n'.join(work_row(w, i) for i, w in enumerate(reversed(works), 1))
    latest_link = f'''<a class="latest-link" href="stories/{latest.slug}.html"><span>最新話 · 約{latest.reading_minutes}分</span><strong>{e(chapter_title(latest))}</strong>{arrow()}</a>''' if featured.ongoing else ''
    return page('Mini Novels', f'''
    <div class="shell">{continue_slot('')}
      <section class="home-feature" aria-labelledby="featured-title">
        <div class="feature-main">
          <div class="feature-caption"><span class="eyebrow">{e(featured.genre)} / {e(featured.status)}</span><span class="feature-index" aria-hidden="true">01 —</span></div>
          <h1 id="featured-title">{cover_title(featured.title)}</h1>
          <p class="feature-description">{e(featured.description)}</p>
          <div class="feature-actions"><a class="button primary" href="stories/{first.slug}.html">{'第一話から読む' if featured.ongoing else 'はじめから読む'} <span aria-hidden="true">→</span></a>
          <a class="text-link" href="{featured.href}">作品の目次 {arrow()}</a></div>
        </div>
        <aside class="feature-side"><div class="opening"><span class="eyebrow">物語のはじまり</span>
          <blockquote>{opening_quote(first)}</blockquote><span class="opening-source">{e(chapter_title(first))} より</span></div>{latest_link}</aside>
      </section>
      <section class="library" id="library" aria-labelledby="library-title">
        <div class="section-heading"><div><span class="eyebrow">THE COLLECTION</span><h2 id="library-title">物語を選ぶ<span class="count">{len(works):02d}</span></h2></div><p>連載・中編 {len(works)-short_count}作品 / 短編 {short_count}作品</p></div>
        <div class="library-tools js-only"><div class="filter-group" role="group" aria-label="作品の種類"><button data-filter="all" aria-pressed="true">すべて</button><button data-filter="serial" aria-pressed="false">連載・中編</button><button data-filter="short" aria-pressed="false">短編</button></div>
          <label class="search-label"><span aria-hidden="true">⌕</span><span class="sr-only">作品名や言葉で探す</span><input type="search" id="library-search" placeholder="作品名や言葉で探す" autocomplete="off"></label></div>
        <p class="search-status sr-only" role="status" aria-live="polite"></p>
        <ol class="work-list">{rows}</ol>
        <p class="empty-search" hidden>見つかりませんでした。別の言葉で探してみてください。<button class="text-link" data-reset-search>検索をリセット</button></p>
      </section>
      <aside class="home-colophon"><span class="eyebrow">MINI NOVELS</span><p>ひとつずつ書き、読み、育てていく。<br>短編と、続いていく物語のための場所です。</p><a class="text-link" href="about.html">この場所について {arrow()}</a></aside>
    </div>''', 'index.html')


def work_page(work):
    first, latest = work.stories[0], work.stories[-1]
    rows = '\n'.join(f'''<li><a href="../stories/{s.slug}.html"><span class="chapter-number">{i:02d}</span><span class="chapter-name">{e(chapter_title(s))}</span><span class="chapter-time">約{s.reading_minutes}分 <span aria-hidden="true">→</span></span></a></li>''' for i, s in enumerate(work.stories, 1))
    latest_link = f'<a class="text-link" href="../stories/{latest.slug}.html">最新話を読む {arrow()}</a>' if work.ongoing else ''
    return page(work.title, f'''<div class="shell work-page">
      <a class="breadcrumb" href="../index.html#library">← 作品一覧</a>{continue_slot('../', work.slug)}
      <div class="book-layout"><header class="book-head"><span class="eyebrow">{e(work.genre)} / {e(work.status)}</span>
      <h1>{cover_title(work.title)}</h1><p class="book-description">{e(work.description)}</p>
      <p class="muted">{'公開分' if work.ongoing else '全編'} 約{work.minutes}分</p>
      <div class="feature-actions"><a class="button primary" href="../stories/{first.slug}.html">はじめから読む <span aria-hidden="true">→</span></a>{latest_link}</div></header>
      <section class="chapter-section" aria-labelledby="chapter-heading"><div class="section-heading"><h2 id="chapter-heading">目次</h2><span class="eyebrow">{len(work.stories):02d} {'EPISODES' if work.ongoing else 'PARTS'}</span></div>
      <ol class="chapter-list">{rows}</ol><p class="series-note">{'物語は続いています。' if work.ongoing else 'この作品は完結しています。'}</p></section></div>
      </div>''', f'works/{work.slug}.html', description=work.description)


def reading_dialogs(story, work):
    sections = ''.join(f'<li><a href="#{s.id}" data-close-dialog>{e(s.title)}</a></li>' for s in story.sections)
    chapters = ''
    if work and work.serial:
        links = []
        for s in work.stories:
            current = ' aria-current="page"' if s.slug == story.slug else ''
            links.append(f'<li><a href="{s.slug}.html"{current}>{e(chapter_title(s))}</a></li>')
        chapters = '<h3>作品の目次</h3><ol class="dialog-chapters">' + ''.join(links) + '</ol>'
    return f'''
    <dialog id="contents-dialog" aria-labelledby="contents-heading"><div class="dialog-heading"><h2 id="contents-heading">目次</h2><button class="close-dialog" data-close-dialog aria-label="目次を閉じる">×</button></div>
    <nav aria-label="読書の目次"><h3>この{'編' if work and work.serial and not work.ongoing else '話'}の中で</h3><ol class="dialog-sections"><li><a href="#main" data-close-dialog>はじめへ</a></li>{sections}</ol>{chapters}</nav></dialog>
    <dialog id="settings-dialog" aria-labelledby="settings-heading"><div class="dialog-heading"><h2 id="settings-heading">読みやすさ</h2><button class="close-dialog" data-close-dialog aria-label="設定を閉じる">×</button></div>
    <fieldset><legend>文字の大きさ</legend><div class="setting-options" data-setting="size"><button data-value="small">小</button><button data-value="medium">標準</button><button data-value="large">大</button><button data-value="xlarge">特大</button></div></fieldset>
    <fieldset><legend>書体</legend><div class="setting-options" data-setting="font"><button data-value="serif" class="serif">明朝</button><button data-value="sans">ゴシック</button></div></fieldset>
    <fieldset><legend>背景</legend><div class="setting-options theme-options" data-setting="theme"><button data-value="light">白</button><button data-value="paper">生成り</button><button data-value="night">夜</button></div></fieldset>
    <p class="settings-note" id="storage-note">設定と読んだ位置は、このブラウザにだけ保存します。</p>
    <button class="text-link" id="reset-settings">標準の表示に戻す</button></dialog>'''


def add_paragraph_anchors(body):
    count = 0
    def replace(match):
        nonlocal count
        count += 1
        return f'<{match.group(1)} id="p-{count}"{match.group(2)}>'
    return re.sub(r'<(p|blockquote|ul|ol)([^>]*)>', replace, body)


def story_page(story, work, all_works, *, archive=False, counterpart=False):
    prefix = '../../' if archive else '../'
    path = f"{'archive/' if archive else ''}stories/{story.slug}.html"
    within = work.stories.index(story) if work else 0
    previous = work.stories[within - 1] if work and within else None
    next_story = work.stories[within + 1] if work and within + 1 < len(work.stories) else None
    title = chapter_title(story) if work and work.serial else story.title
    book_link = f'<a href="../{work.href}">{e(work.title)}</a>' if work and work.serial else '<span>短編小説</span>'
    if archive:
        book_link = '<a href="../index.html">初期版アーカイブ</a>'
    body = add_paragraph_anchors(story.html_body)
    if counterpart:
        counterpart_href = f'../../stories/{story.slug}.html' if archive else f'../archive/stories/{story.slug}.html'
        edition = f'<p class="edition-link"><a href="{counterpart_href}">{"現行版を読む" if archive else "初期版を読む"} {arrow()}</a></p>'
    else:
        edition = ''
    if next_story:
        onward = f'<a class="next-story" href="{next_story.slug}.html"><span class="eyebrow">続きへ</span><strong>{e(chapter_title(next_story))}</strong><span aria-hidden="true">→</span></a>'
    elif work and work.ongoing:
        onward = f'<p class="end-note">公開されている話は、ここまで。<br>続きは、作品の目次から。</p><a class="button" href="../{work.href}">作品の目次へ <span aria-hidden="true">→</span></a>'
    else:
        onward = '<p class="end-mark" aria-label="おわり">了</p>'
        if not archive and all_works:
            related = {'001': '002', '005': '006', '006': '005', '010': '011', '011': '012'}
            target = related.get(work.stories[0].sequence_label) if work else None
            recommended = next((w for w in all_works if w.stories[0].sequence_label == target), None)
            recommended = recommended or next((w for w in reversed(all_works) if w != work), None)
            if recommended:
                onward += f'<a class="next-story recommendation" href="{prefix}{recommended.href}"><span class="eyebrow">もう一冊、読むなら</span><strong>{e(recommended.title)}</strong><span aria-hidden="true">→</span></a>'
    previous_link = f'<a href="{previous.slug}.html">← {e(chapter_title(previous))}</a>' if previous else ''
    toc_link = f'<a href="../{work.href}">作品の目次</a>' if work and work.serial else f'<a href="{prefix}index.html#library">作品一覧へ</a>'
    if archive:
        toc_link = '<a href="../index.html">初期版の目次へ</a>'
    initial_notice = '<p class="archive-notice">このページは、改稿前の初期版です。</p>' if archive else ''
    metadata = {'id': ('archive/' if archive else '') + story.slug,
                'title': story.title, 'url': path, 'minutes': story.reading_minutes,
                'next': {'url': f'stories/{next_story.slug}.html', 'title': next_story.title} if next_story else None,
                'work': work.slug if work else None}
    data = json.dumps(metadata, ensure_ascii=False).replace('<', '\\u003c')
    return page(story.title, f'''
      <article class="reader" data-story="{e(story.slug)}">
        <header class="story-head"><div class="story-context">{book_link}</div>{initial_notice}
          <h1>{e(title)}</h1><p class="story-meta">約{story.reading_minutes}分<span aria-hidden="true"> / </span>{story.character_count:,}字</p>
          <div class="resume-notice" hidden><span>前回読んだ位置が保存されています。</span><button id="resume-reading">続きから読む ↓</button></div>
        </header>
        <div class="story-body" id="story-body">{body}</div>
        <footer class="story-end" id="story-end">{onward}<nav class="end-navigation" aria-label="作品間の移動">{previous_link}{toc_link}</nav>{edition}</footer>
      </article>
      <div class="reader-controls js-only" role="group" aria-label="読書ツール">
        <button data-dialog="contents-dialog"><span aria-hidden="true">☰</span> 目次</button><div class="reading-progress"><span class="sr-only">読書の進み具合</span><span id="progress-label">0%</span><div class="progress-track" aria-hidden="true"><span id="progress-fill"></span></div></div><button data-dialog="settings-dialog"><span class="type-icon" aria-hidden="true">あ</span> 表示</button>
      </div>{reading_dialogs(story, work)}
      <script type="application/json" id="story-data">{data}</script>''', path, description=work.description if work else story.description, reader=True)


def archive_page(stories):
    rows = ''.join(f'<li class="archive-row"><span>{e(s.sequence_label)}</span><a href="stories/{s.slug}.html">{e(s.title)} {arrow()}</a><span>約{s.reading_minutes}分</span></li>' for s in stories)
    return page('初期版アーカイブ', f'''<div class="shell narrow-page"><a class="breadcrumb" href="../index.html">← ホーム</a><header class="page-intro"><span class="eyebrow">INITIAL EDITION</span><h1>初期版アーカイブ</h1><p>同じ題から、違う物語へ。<br>改稿前の作品を、そのまま残しています。</p></header><ol class="archive-list">{rows}</ol></div>''', 'archive/index.html', description='Mini Novelsの改稿前の作品を保存した初期版アーカイブです。')


def about_page():
    return page('この場所について', '''<div class="shell about-page"><a class="breadcrumb" href="index.html">← ホーム</a>
      <header class="page-intro"><span class="eyebrow">ABOUT MINI NOVELS</span><h1>ひとつずつ、<br>物語を育てる。</h1></header>
      <div class="about-body"><p>Mini Novelsは、短編小説と連載小説を公開する、小さな作品集です。</p>
      <p>一人の人間が問いや方向を差し出し、AIが書き、対話を重ねながら次の作品へ進む。そうした協働の中から生まれた小説を、ここに置いています。</p>
      <p>一作で読み終える短編も、登場人物と長く過ごす連載もあります。気になる題を、ひとつ開いてみてください。</p>
      <h2>読むためのこと</h2><p>読書画面の「表示」から、文字の大きさ、書体、背景色を変えられます。途中で閉じた作品は、次に訪れたときに読んでいた位置から再開できます。</p>
      <p>設定と読書位置は、お使いのブラウザの中だけに保存します。会員登録はありません。別の端末との同期は行いません。ブラウザのデータを消すと、保存した位置も消えます。</p>
      <p>本文はJavaScriptを無効にしていても読めます。日本語の書体はGoogle Fontsから読み込み、接続できない場合は端末の書体で表示します。</p>
      <h2>初期版について</h2><p>改稿前の小説は、<a href="archive/index.html">初期版アーカイブ</a>に残しています。同じ題でも、現在の作品とは内容が異なります。</p>
      <a class="button primary" href="index.html#library">作品を選ぶ <span aria-hidden="true">→</span></a></div></div>''', 'about.html')


def build_site():
    global ASSET_VERSION, READING_INDEX
    importlib.reload(manuscripts)
    asset_dir = ROOT / 'web'
    ASSET_VERSION = sha256(b''.join(p.read_bytes() for p in sorted(asset_dir.glob('*')) if p.is_file())).hexdigest()[:10]
    stories = [manuscripts.load_story(p) for p in sorted((ROOT / 'stories').glob('*.md'))]
    archived = [manuscripts.load_story(p) for p in sorted((ROOT / 'archive/initial').glob('*.md'))]
    works = collect_works(stories)
    READING_INDEX = {}
    for work in works:
        for i, story in enumerate(work.stories):
            next_story = work.stories[i + 1] if i + 1 < len(work.stories) else None
            READING_INDEX[f'stories/{story.slug}.html'] = {
                'next': {'url': f'stories/{next_story.slug}.html', 'title': next_story.title} if next_story else None}
    for story in archived:
        READING_INDEX[f'archive/stories/{story.slug}.html'] = {'next': None}
    pages = {'index.html': home(works), 'about.html': about_page(), 'archive/index.html': archive_page(archived)}
    archived_slugs = {s.slug for s in archived}
    current_slugs = {s.slug for s in stories}
    for work in works:
        if work.serial:
            pages[work.href] = work_page(work)
        for story in work.stories:
            pages[f'stories/{story.slug}.html'] = story_page(story, work, works, counterpart=story.slug in archived_slugs)
    for story in archived:
        pages[f'archive/stories/{story.slug}.html'] = story_page(story, None, works, archive=True, counterpart=story.slug in current_slugs)
    pages['404.html'] = page('ページが見つかりません', '<div class="shell page-intro"><h1>ページが見つかりません。</h1><p>作品の一覧から、読みたい小説をお探しください。</p><a class="button primary" href="' + PUBLIC_URL + '">作品一覧へ →</a></div>', '404.html')
    # Prepare all page strings before replacing existing generated pages.
    SITE.mkdir(exist_ok=True)
    for relative, html in pages.items():
        output = SITE / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding='utf-8')
    for old in SITE.rglob('*.html'):
        if old.relative_to(SITE).as_posix() not in pages:
            old.unlink()
    shutil.copytree(asset_dir, SITE / 'assets', dirs_exist_ok=True)
    (SITE / '.nojekyll').write_text('', encoding='utf-8')
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{PUBLIC_URL}{p}</loc></url>' for p in pages if p != '404.html') + '</urlset>\n'
    (SITE / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    print(f'Built {len(works)} works, {len(stories)} current chapters, {len(archived)} initial editions; {len(pages)} pages.')


if __name__ == '__main__':
    build_site()
