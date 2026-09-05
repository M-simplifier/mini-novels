"""Check the generated publication, including links into archived editions."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import build_site
import manuscripts


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ids = []
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if 'id' in attributes:
            self.ids.append(attributes['id'])
        for key in ('href', 'src'):
            if key in attributes:
                self.links.append(attributes[key])


class PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_site.build_site()
        cls.site = ROOT / 'site'
        cls.docs = {p: Document(p.read_text(encoding='utf-8')) for p in cls.site.rglob('*.html')}

    def test_every_local_link_and_fragment_resolves(self):
        for source, document in self.docs.items():
            self.assertEqual(len(document.ids), len(set(document.ids)), str(source))
            for href in document.links:
                with self.subTest(page=source.name, href=href):
                    url = urlsplit(href)
                    if url.scheme or url.netloc or url.fragment == 'resume':
                        continue
                    target = (source.parent / unquote(url.path)).resolve() if url.path else source
                    if target.is_dir():
                        target /= 'index.html'
                    self.assertTrue(target.is_relative_to(self.site.resolve()), str(target))
                    self.assertTrue(target.is_file(), str(target))
                    if url.fragment:
                        self.assertIn(unquote(url.fragment), self.docs[target].ids)

    def test_every_manuscript_and_section_is_published(self):
        for source_dir, output_dir in [('stories', 'stories'), ('archive/initial', 'archive/stories')]:
            for source in (ROOT / source_dir).glob('*.md'):
                story = manuscripts.load_story(source)
                output = self.site / output_dir / f'{source.stem}.html'
                self.assertIn(output, self.docs)
                for section in story.sections:
                    self.assertIn(section.id, self.docs[output].ids)
                html = output.read_text(encoding='utf-8')
                # Strip only the newly added paragraph anchors, leaving original HTML intact.
                import re
                body = html.split('<div class="story-body" id="story-body">', 1)[1].split('</div>', 1)[0]
                self.assertEqual(re.sub(r' id="p-\d+"', '', body), story.html_body)

    def test_work_grouping_and_new_episode(self):
        from dataclasses import replace
        stories = [manuscripts.load_story(p) for p in sorted((ROOT / 'stories').glob('*.md'))]
        works = build_site.collect_works(stories)
        self.assertEqual(sum(len(w.stories) for w in works), len(stories))
        finished = next(w for w in works if w.slug == 'my-own-work')
        serial = next(w for w in works if w.slug == 'ship-without-a-front')
        self.assertEqual(len(finished.stories), 3)
        self.assertFalse(finished.ongoing)
        self.assertTrue(serial.ongoing)
        last = serial.stories[-1]
        additional = replace(last, slug='999_test_next_episode', episode=last.episode + 1,
                             sequence_label='999', title=last.series + ' 次話「試験」')
        insert_at = stories.index(last) + 1
        updated = build_site.collect_works(stories[:insert_at] + [additional] + stories[insert_at:])
        self.assertEqual(len(updated), len(works))
        new_serial = next(w for w in updated if w.slug == serial.slug)
        self.assertEqual(len(new_serial.stories), len(serial.stories) + 1)
        last_page = build_site.story_page(last, new_serial, updated)
        self.assertIn('href="999_test_next_episode.html"', last_page)
        self.assertNotIn('公開されている話は、ここまで', last_page)

    def test_latest_is_ongoing_and_finished_story_is_finished(self):
        stories = [manuscripts.load_story(p) for p in sorted((ROOT / 'stories').glob('*.md'))]
        serial = next(w for w in build_site.collect_works(stories) if w.slug == 'ship-without-a-front')
        latest = (self.site / f'stories/{serial.stories[-1].slug}.html').read_text(encoding='utf-8')
        finished = (self.site / 'stories/015_my_own_work_part_3.html').read_text(encoding='utf-8')
        self.assertIn('公開されている話は、ここまで', latest)
        self.assertNotIn('class="end-mark"', latest)
        self.assertIn('class="end-mark"', finished)
        self.assertNotIn('次の話:', finished)

    def test_404_uses_public_base_at_any_depth(self):
        html = (self.site / '404.html').read_text(encoding='utf-8')
        self.assertIn(f'<base href="{build_site.PUBLIC_URL}">', html)


if __name__ == '__main__':
    unittest.main()
