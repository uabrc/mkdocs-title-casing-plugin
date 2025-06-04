from __future__ import annotations

import unittest

from mkdocs_title_casing_plugin.string_helpers import (
    is_term_ignored,
    parse_html_heading,
    to_ignored_terms_mapping,
)


class TestFreeFunctions(unittest.TestCase):
    def test_ignore_term(self):
        ignored_terms = to_ignored_terms_mapping(
            [
                "FAQ",
                "`echo`",
                "mv",
                "s3cmd",
                "iPad",
            ],
        )

        def check(term: str) -> str | None:
            return is_term_ignored(ignored_terms, term)

        # NOT IN IGNORE LIST
        self.assertEqual(check("(`cat`)"), None)
        self.assertEqual(check("`cat`"), None)
        self.assertEqual(check("cat"), None)

        # IN IGNORE LIST
        self.assertEqual(check("(`mv`)"), "(`mv`)")
        self.assertEqual(check("`mv`"), "`mv`")
        self.assertEqual(check("Mv"), "mv")
        self.assertEqual(check("mv"), "mv")

        self.assertEqual(check("FAQ"), "FAQ")
        self.assertEqual(check("Faq"), "FAQ")
        self.assertEqual(check("(FAQ)"), "(FAQ)")

        self.assertEqual(check("s3cmd"), "s3cmd")
        self.assertEqual(check("S3CMD"), "s3cmd")
        self.assertEqual(check("S3cmd"), "s3cmd")

        self.assertEqual(check("iPad"), "iPad")
        self.assertEqual(check("IPAD"), "iPad")
        self.assertEqual(check("ipad"), "iPad")

        # PUNCTUATED VERSION IN IGNORE LIST
        self.assertEqual(check("Echo"), None)
        self.assertEqual(check("echo"), None)
        self.assertEqual(check("(`echo`)"), "(`echo`)")
        self.assertEqual(check("`(echo)`"), "`(echo)`")
        self.assertEqual(check("`(echo`)"), "`(echo`)")
        self.assertEqual(check("`echo`"), "`echo`")

    def test_parse_html_heading(self):
        def parse(line: str) -> tuple[str, str, str] | None:
            return parse_html_heading(line)

        self.assertEqual(
            parse(
                '<h6 id="id">heading 6<a class="headerlink" href="#heading-6">&para;</a></h1>',
            ),
            (
                '<h6 id="id">',
                "heading 6",
                '<a class="headerlink" href="#heading-6">&para;</a></h1>',
            ),
        )

        self.assertEqual(
            parse(
                '<h5 id="id">heading 5<a class="headerlink" href="#heading-5">&para;</a></h1>',
            ),
            (
                '<h5 id="id">',
                "heading 5",
                '<a class="headerlink" href="#heading-5">&para;</a></h1>',
            ),
        )

        self.assertEqual(
            parse(
                '<h4 id="id">heading 4<a class="headerlink" href="#heading-4">&para;</a></h1>',
            ),
            (
                '<h4 id="id">',
                "heading 4",
                '<a class="headerlink" href="#heading-4">&para;</a></h1>',
            ),
        )

        self.assertEqual(
            parse(
                '<h3 id="id">heading 3<a class="headerlink" href="#heading-3">&para;</a></h1>',
            ),
            (
                '<h3 id="id">',
                "heading 3",
                '<a class="headerlink" href="#heading-3">&para;</a></h1>',
            ),
        )

        self.assertEqual(
            parse(
                '<h2 id="id">heading 2<a class="headerlink" href="#heading-2">&para;</a></h1>',
            ),
            (
                '<h2 id="id">',
                "heading 2",
                '<a class="headerlink" href="#heading-2">&para;</a></h1>',
            ),
        )

        self.assertEqual(
            parse(
                '<h1 id="id">heading 1<a class="headerlink" href="#heading-1">&para;</a></h1>',
            ),
            (
                '<h1 id="id">',
                "heading 1",
                '<a class="headerlink" href="#heading-1">&para;</a></h1>',
            ),
        )

        self.assertEqual(
            parse(
                '<h1 id="id"><code>cat</code><a class="headerlink" href="#heading-1">&para;</a></h1>',
            ),
            (
                '<h1 id="id">',
                "`cat`",
                '<a class="headerlink" href="#heading-1">&para;</a></h1>',
            ),
        )

        self.assertEqual(parse("<ol>"), None)
