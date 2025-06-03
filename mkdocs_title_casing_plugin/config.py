"""Helpers for handling non-standard config values."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.config import config_options
from mkdocs.config.base import Config

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


class TitleCasingPluginConfig(Config):
    """Config for this plugin."""

    mode = config_options.Type(str, default="warn")
    capitalization_type = config_options.Type(str, default="title")
    default_page_name = config_options.Type(str, default="Home")


def find_nav_line_number_in_config(config: MkDocsConfig) -> int | None:
    """Find the starting line number of the nav entry in the config file."""
    with Path(config.config_file_path).open("r") as f:
        lines = f.readlines()

    for n, line in enumerate(lines, start=2):
        if line.startswith("nav:"):
            return n

    return None
