"""Title Case plugin."""

from __future__ import annotations

import abc
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.exceptions import ConfigurationError
from mkdocs.plugins import BasePlugin
from mkdocs.structure import StructureItem
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Link, Navigation, Section
from mkdocs.structure.pages import Page
from titlecase import titlecase

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files

log = logging.getLogger(f"mkdocs.plugins.{__name__}")

Item = Section | Page | Link | StructureItem

html_heading_re = re.compile(
    r"^([ \t]*<(?:h1|h2|h3|h4|h5|h6)[ \t]+(?:.*?=[^>]*?)>)"  # prefix: "<h1 id="id">""
    r"(.*?)"  # heading: "this IS a Heading"
    r"(<.*)$",  # suffix: "<a>&para;</h1>"
)
markdown_heading_re = re.compile(r"^(#+[ \t])(.*)$")


class TitleCasingPluginConfig(Config):
    """Config for this plugin."""

    mode = config_options.Type(str, default="warn")
    capitalization_type = config_options.Type(str, default="title")
    default_page_name = config_options.Type(str, default="Home")


class TitleCasingPlugin(BasePlugin[TitleCasingPluginConfig]):
    """Plugin to check and warn of title case issues."""

    def __init__(self) -> None:
        """Initialize TitleCasingPlugin object."""
        self._nav_starting_line_number: int = 0

    def on_config(self, config: MkDocsConfig) -> None:
        """Gather initialization information from config."""
        if config.nav is None:
            return

        lines: list[str]
        with Path(config.config_file_path).open("r") as f:
            lines = f.readlines()

        for n, line in enumerate(lines, start=2):
            if line.startswith("nav:"):
                self._nav_starting_line_number = n
                break

    def on_nav(
        self,
        nav: Navigation,
        config: MkDocsConfig,
        files: Files,  # noqa: ARG002 | required by BasePlugin
    ) -> Navigation | None:
        """Check and warn of title case issues in nav titles."""
        if config.nav is None:
            return None

        mode = self.config.mode
        if mode == "fix":
            strategy = FixOnNavStrategy(self.config)
        elif mode == "warn":
            strategy = WarningOnNavStrategy(self.config, self.config.config_file_path)
        else:
            msg = f"Unexpected mode: {mode}"
            raise ConfigurationError(msg)

        return strategy.on_nav(nav, self._nav_starting_line_number)

    def on_page_content(
        self,
        html: str,
        /,
        *,
        page: Page,
        config: MkDocsConfig,  # noqa: ARG002 | required by BasePlugin
        files: Files,  # noqa: ARG002 | required by BasePlugin
    ) -> str | None:
        """Fix title case issues in page headings in HTML.

        Diagnostic line numbers would only be useful for on_page_markdown() and
        would require a markdown parser with source position. Python-markdown
        does not have that feature, and other parsers do not understand mkdocs
        extensions.
        """
        mode = self.config.mode
        if mode == "fix":
            strategy = FixOnPageContentStrategy(self.config)
        elif mode == "warn":
            strategy = WarningOnPageContentStrategy(self.config)
        else:
            msg = f"Unexpected mode: {mode}"
            raise ConfigurationError(msg)

        return strategy.on_page_content(html, page.file.src_path)


class Strategy:
    """Base class for all strategies."""

    def __init__(self, config: TitleCasingPluginConfig) -> None:
        """Initialize new Strategy."""
        self._config = config

    def _handle_heading(
        self,
        heading: str | None,
        line_number: int | None = None,
        file_path: str | None = None,
    ) -> None:
        if heading is None:
            return

        fixed_heading = self._to_titlecase(heading)
        if heading != fixed_heading:
            msg = 'Heading "%s" should be "%s".'
            args = (heading, fixed_heading)

            if line_number is not None:
                msg = "(%d): " + msg
                args = (line_number, *args)

            if file_path:
                msg = "%s: " + msg
                args = (file_path, *args)

            log.warning(msg, *args)

    def _to_titlecase(self, _v: str) -> str:
        _v = _v.strip()

        capitalization_type = self._config.capitalization_type

        if capitalization_type == "first_letter":
            out = _v.title()
        elif capitalization_type == "title":
            out = titlecase(_v)
        else:
            msg = f"Unexpected capitalization_type: {capitalization_type}."
            raise ConfigurationError(msg)

        return out.strip()


class OnNavStrategy(Strategy, abc.ABC):
    """Base class for on_nav()."""

    def on_nav(self, nav: Navigation, initial_line_number: int) -> Navigation | None:
        """Call in client method of the same name."""
        line_number = initial_line_number
        for child in nav:
            out_child, line_number = self._traverse_navigation(child, line_number)
            self._handle_top_level_item(out_child)

        return self._build_output()

    def _traverse_navigation(
        self,
        item: Item,
        line_number: int,
    ) -> tuple[Item, int]:
        if isinstance(item, Section):
            out_item, line_number = self._traverse_section(item, line_number)
        elif isinstance(item, Page):
            out_item = self._handle_page(item, line_number)
        elif isinstance(item, Link):
            out_item = self._handle_link(item, line_number)
        else:
            log.debug("unknown type: %s", type(item))
            out_item = item

        return out_item, line_number + 1

    def _traverse_section(
        self,
        section: Section,
        line_number: int,
    ) -> tuple[Section, int]:
        out_children: list[Item] = []
        for child in section.children:
            out_child, line_number = self._traverse_navigation(child, line_number)
            out_children.append(out_child)

        out_section = self._handle_section(section, out_children, line_number)

        return out_section, line_number

    @abc.abstractmethod
    def _handle_section(
        self,
        section: Section,
        out_children: list[Item],
        line_number: int,
    ) -> Section: ...

    @abc.abstractmethod
    def _handle_page(self, page: Page, line_number: int) -> Page: ...

    @abc.abstractmethod
    def _handle_top_level_item(self, out_item: Item) -> None: ...

    @abc.abstractmethod
    def _handle_link(
        self,
        link: Link,
        line_number: int,
    ) -> Link: ...

    @abc.abstractmethod
    def _build_output(self) -> Navigation | None: ...


class WarningOnNavStrategy(OnNavStrategy):
    """Warn about heading case in on_nav()."""

    def __init__(self, config: TitleCasingPluginConfig, config_file_path: str) -> None:
        """Initialize WarningOnNavStrategy object."""
        super().__init__(config)
        self._config_file_path = config_file_path

    def _before_section(self) -> None:
        pass

    def _handle_section(
        self,
        section: Section,
        _out_children: list[Item],
        line_number: int,
    ) -> Section:
        self._handle_structure_item(section, line_number)
        return section

    def _after_section(self, _out_section: Section) -> None:
        pass

    def _handle_page(self, page: Page, line_number: int) -> Page:
        self._handle_structure_item(page, line_number)
        return page

    def _handle_top_level_item(self, out_item: Item) -> None:
        pass

    def _handle_link(self, link: Link, line_number: int) -> Link:
        self._handle_structure_item(link, line_number)
        return link

    def _handle_structure_item(
        self, item: Section | Page | Link, line_number: int
    ) -> None:
        self._handle_heading(
            item.title,  # pyright: ignore[reportArgumentType]
            line_number=line_number,
            file_path=self._config_file_path,
        )

    def _build_output(self) -> None:
        pass


class FixOnNavStrategy(OnNavStrategy):
    """Fixes heading case in on_nav()."""

    def __init__(self, config: TitleCasingPluginConfig) -> None:
        """Initialize FixNavStrategy object."""
        super().__init__(config)
        self._pages: list[Page] = []
        self._items: list[Item] = []

    def _handle_section(
        self,
        section: Section,
        _out_children: list[Item],
        _line_number: int,
    ) -> Section:
        heading: str = section.title
        fixed_heading = self._to_titlecase(heading)
        return Section(fixed_heading, _out_children)

    def _handle_page(self, page: Page, _line_number: int) -> Page:
        heading: str | None = page.title  # pyright: ignore[reportAssignmentType]
        fixed_heading = self._to_titlecase(heading) if heading is not None else heading
        new_page = Page(
            fixed_heading,
            page.file,
            self._config,  # pyright: ignore[reportArgumentType]
        )
        self._pages.append(new_page)
        return new_page

    def _handle_top_level_item(self, out_item: Item) -> None:
        self._items.append(out_item)

    def _handle_link(self, link: Link, _line_number: int) -> Link:
        heading: str = link.title
        fixed_heading = self._to_titlecase(heading) if heading is not None else heading
        new_link = Link(fixed_heading, link.url)
        self._items.append(new_link)
        return new_link

    def _build_output(self) -> Navigation | None:
        return Navigation(self._items, self._pages)


class OnPageContentStrategy(Strategy, abc.ABC):
    """Base class for on_page_markdown()."""

    def on_page_content(self, html: str, file_path: str) -> str | None:
        """Warn of title case issues in page headings in rendered HTML.

        I've chosen to
        """
        for line in html.splitlines():
            match = html_heading_re.fullmatch(line)
            if match is not None:
                self._handle_markdown_heading_line(
                    match[1],
                    match[2],
                    match[3],
                    file_path,
                )
            else:
                self._handle_markdown_nonheading_line(line, file_path)

        return self._build_output()

    @abc.abstractmethod
    def _handle_markdown_nonheading_line(self, line: str, file_path: str) -> None: ...

    @abc.abstractmethod
    def _handle_markdown_heading_line(
        self,
        prefix: str,
        heading: str,
        postfix: str,
        file_path: str,
    ) -> None: ...

    @abc.abstractmethod
    def _build_output(self) -> str | None: ...


class WarningOnPageContentStrategy(OnPageContentStrategy):
    """Warn about heading case in on_page_markdown()."""

    def _handle_markdown_nonheading_line(self, _line: str, _file_path: str) -> None:
        pass

    def _handle_markdown_heading_line(
        self,
        _prefix: str,
        heading: str,
        _suffix: str,
        file_path: str,
    ) -> None:
        self._handle_heading(heading, file_path=file_path)

    def _build_output(self) -> None:
        pass


class FixOnPageContentStrategy(OnPageContentStrategy):
    """Fix heading case in on_page_markdown()."""

    def __init__(self, config: TitleCasingPluginConfig) -> None:
        """Initialize FixPageMarkdownStrategy object."""
        super().__init__(config)
        self._lines: list[str] = []

    def _handle_markdown_nonheading_line(self, line: str, _file_path: str) -> None:
        self._lines.append(line)

    def _handle_markdown_heading_line(
        self,
        prefix: str,
        heading: str,
        suffix: str,
        _file_path: str,
    ) -> None:
        fixed_heading = self._to_titlecase(heading)
        self._lines.append(prefix + fixed_heading + suffix)

    def _build_output(self) -> str:
        return "\n".join(self._lines)
