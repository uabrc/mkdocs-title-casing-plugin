"""Helpers for handling non-standard config values."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.config import config_options
from mkdocs.config.base import Config

from mkdocs_title_casing_plugin.string_helpers import (
    Term,
)

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


class TitleCasingPluginConfig(Config):
    """Config for this plugin."""

    mode = config_options.Type(str, default="warn")
    capitalization_type = config_options.Type(str, default="title")
    ignore_definition_file = config_options.Type(str, default=".title-casing-ignore")


def find_nav_line_number_in_config(config: MkDocsConfig) -> int | None:
    """Find the starting line number of the nav entry in the config file."""
    with Path(config.config_file_path).open("r") as f:
        lines = f.readlines()

    for n, line in enumerate(lines, start=2):
        if line.startswith("nav:"):
            return n

    return None


def prepare_ignored_terms(
    config: TitleCasingPluginConfig,
) -> dict[Term, Term]:
    """Prepare casefold-to-canonical mapping."""
    if Path(config.ignore_definition_file).exists():
        with Path(config.ignore_definition_file).open("r") as f:
            terms_to_ignore = [Term.from_string(line.strip()) for line in f]
    else:
        terms_to_ignore = []

    return {term.to_lookup_form(): term for term in terms_to_ignore}
