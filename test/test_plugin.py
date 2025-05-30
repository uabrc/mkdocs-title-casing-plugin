from __future__ import annotations

import logging
import textwrap
import unittest
from pathlib import PurePath
from typing import TYPE_CHECKING

from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Link, Navigation, Section
from mkdocs.structure.pages import Page

from mkdocs_title_casing_plugin.plugin import (
    Item,
    TitleCasingPlugin,
    TitleCasingPluginConfig,
)

if TYPE_CHECKING:
    from mkdocs.config.base import Config


class LogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._entries: list[str] = []

        log = logging.getLogger("mkdocs.plugins.mkdocs_title_casing_plugin.plugin")
        log.addHandler(self)

    @property
    def entries(self) -> list[str]:
        return self._entries

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)
        self._entries.append(log_entry)


class TestStrategies(unittest.TestCase):
    def setUp(self) -> None:
        config = TitleCasingPluginConfig()
        # dummy nav to bypass "nav is None" guards
        config.nav = ""  # pyright: ignore[reportAttributeAccessIssue]
        self._config = config

        html = """
            <h1 id="id">heading 1<a class="headerlink" href="#heading-1">&para;</a></h1>
            <h2 id="id">heading 2<a class="headerlink" href="#heading-2">&para;</a></h1>
            <h3 id="id">heading 3<a class="headerlink" href="#heading-3">&para;</a></h1>
            <h4 id="id">heading 4<a class="headerlink" href="#heading-4">&para;</a></h1>
            <h5 id="id">heading 5<a class="headerlink" href="#heading-5">&para;</a></h1>
            <h6 id="id">heading 6<a class="headerlink" href="#heading-6">&para;</a></h1>
            <ul>
            <li>item 1</li>
            </ul>
            <ol>
            <li>item 2</li>
            </ol>
            """
        self._html = textwrap.dedent(html).strip()

        expected_html = """
            <h1 id="id">Heading 1<a class="headerlink" href="#heading-1">&para;</a></h1>
            <h2 id="id">Heading 2<a class="headerlink" href="#heading-2">&para;</a></h1>
            <h3 id="id">Heading 3<a class="headerlink" href="#heading-3">&para;</a></h1>
            <h4 id="id">Heading 4<a class="headerlink" href="#heading-4">&para;</a></h1>
            <h5 id="id">Heading 5<a class="headerlink" href="#heading-5">&para;</a></h1>
            <h6 id="id">Heading 6<a class="headerlink" href="#heading-6">&para;</a></h1>
            <ul>
            <li>item 1</li>
            </ul>
            <ol>
            <li>item 2</li>
            </ol>
            """
        self._expected_html = textwrap.dedent(expected_html).strip()

        expected_dir = str(PurePath("dir\\file.md"))
        expected_html_log_entries = [
            ': Heading "heading 1" should be "Heading 1".',
            ': Heading "heading 2" should be "Heading 2".',
            ': Heading "heading 3" should be "Heading 3".',
            ': Heading "heading 4" should be "Heading 4".',
            ': Heading "heading 5" should be "Heading 5".',
            ': Heading "heading 6" should be "Heading 6".',
        ]
        expected_html_log_entries = [
            expected_dir + e for e in expected_html_log_entries
        ]
        self._expected_html_log_entries = expected_html_log_entries
        make = ConfiguredMaker(config)
        self._make = make

        p1 = make.page("page 1")
        p2 = make.page("section 1 page 2")
        p3 = make.page("section 1 page 3")
        p4 = make.page("section 2 section 3 section 4 page 4")
        p5 = make.page("section 2 page 5")
        p6 = make.page("page 6")
        p_null = make.page(None)

        s4 = Section("section 4", [p4])
        s3 = Section("section 3", [s4])
        s2 = Section("section 2", [s3, p5])
        s1 = Section("section 1", [p2, p3])
        s_null = Section("", [p_null])

        link = Link("link", "")
        link_null = Link("", "")

        items = [p1, s1, s2, p6, s_null, link, link_null]
        pages = [p1, p2, p3, p4, p5, p6, p_null]

        self._nav = Navigation(items, pages)

        p1 = make.page("Page 1")
        p2 = make.page("Section 1 Page 2")
        p3 = make.page("Section 1 Page 3")
        p4 = make.page("Section 2 Section 3 Section 4 Page 4")
        p5 = make.page("Section 2 Page 5")
        p6 = make.page("Page 6")
        p_null = make.page("")

        s4 = Section("Section 4", [p4])
        s3 = Section("Section 3", [s4])
        s2 = Section("Section 2", [s3, p5])
        s1 = Section("Section 1", [p2, p3])
        s_null = Section("", [p_null])

        link = Link("link", "")
        link_null = Link("", "")

        items = [p1, s1, s2, p6, s_null, link, link_null]
        pages = [p1, p2, p3, p4, p5, p6, p_null]

        self._expected_nav = Navigation(items, pages)

        self._expected_nav_log_entries = [
            '(0): Heading "page 1" should be "Page 1".',
            '(1): Heading "section 1 page 2" should be "Section 1 Page 2".',
            '(2): Heading "section 1 page 3" should be "Section 1 Page 3".',
            '(3): Heading "section 1" should be "Section 1".',
            '(4): Heading "section 2 section 3 section 4 page 4"'
            ' should be "Section 2 Section 3 Section 4 Page 4".',
            '(5): Heading "section 4" should be "Section 4".',
            '(6): Heading "section 3" should be "Section 3".',
            '(7): Heading "section 2 page 5" should be "Section 2 Page 5".',
            '(8): Heading "section 2" should be "Section 2".',
            '(9): Heading "page 6" should be "Page 6".',
        ]

    def test_fix_on_page_content(self) -> None:
        plugin = TitleCasingPlugin()
        plugin.load_config({"mode": "fix"})
        actual_html = plugin.on_page_content(
            self._html,
            page=self._make.page("dummy", "dir/file.md"),  # pyright: ignore[reportArgumentType]
            config=self._config,  # pyright: ignore[reportArgumentType]
            files=None,  # pyright: ignore[reportArgumentType]
        )

        self.assertEqual(actual_html, self._expected_html)

    def test_warn_on_page_content(self) -> None:
        handler = LogHandler()

        plugin = TitleCasingPlugin()
        plugin.load_config({"mode": "warn"})
        plugin.on_page_content(
            self._html,
            page=self._make.page("dummy", "dir/file.md"),  # pyright: ignore[reportArgumentType]
            config=self._config,  # pyright: ignore[reportArgumentType]
            files=None,  # pyright: ignore[reportArgumentType]
        )
        actual_log_entries = handler.entries

        self.assertEqual(actual_log_entries, self._expected_html_log_entries)

    def test_fix_on_nav(self) -> None:
        plugin = TitleCasingPlugin()
        plugin.load_config({"mode": "fix"})
        actual_nav = plugin.on_nav(
            self._nav,
            self._config,  # pyright: ignore[reportArgumentType]
            Files([]),
        )
        assert actual_nav is not None  # noqa: S101

        actual_item_titles = _flatten_top_level_titles(actual_nav.items)
        expected_item_titles = _flatten_top_level_titles(self._expected_nav.items)
        self.assertEqual(actual_item_titles, expected_item_titles)

        actual_page_titles = [
            item.title if item.title is not None else "" for item in actual_nav.pages
        ]
        expected_page_titles = [item.title for item in self._expected_nav.pages]
        self.assertEqual(actual_page_titles, expected_page_titles)

    def test_warn_on_nav(self) -> None:
        handler = LogHandler()

        plugin = TitleCasingPlugin()
        plugin.load_config({"mode": "warn"})
        plugin.on_nav(
            self._nav,
            self._config,  # pyright: ignore[reportArgumentType]
            Files([]),
        )
        actual_log_entries = handler.entries

        self.assertEqual(actual_log_entries, self._expected_nav_log_entries)


def _flatten_top_level_titles(top_level_items: list[Item]) -> list[str]:
    flattened = [_flatten_titles(top_level_item) for top_level_item in top_level_items]
    return [item for items in flattened for item in items]


def _flatten_titles(item: Item) -> list[str]:
    if isinstance(item, Page):
        t = item.title
        t = t if t is not None else ""
        return [t]  # pyright: ignore[reportReturnType]
    if isinstance(item, Section):
        return [item.title, *_flatten_top_level_titles(item.children)]
    return []


class ConfiguredMaker:
    def __init__(self, config: Config) -> None:
        self._config = config

    def page(self, title: str | None, file_src: str | None = None) -> Page:
        return Page(title, self._make_file(file_src=file_src), self._config)  # pyright: ignore[reportArgumentType]

    def _make_file(self, file_src: str | None = None) -> File:
        path = "" if file_src is None else file_src
        return File(path, file_src, "", True)  # noqa: FBT003
