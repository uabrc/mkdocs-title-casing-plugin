"""Helpers for string operations."""

from __future__ import annotations

import re

PUNCTUATION = r"""!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~"""  # noqa: RUF001
PUNCTUATION_CAPTURE_RE = re.compile(rf"([{PUNCTUATION}]*)(.*?)([{PUNCTUATION}]*)")
HTML_HEADING_RE = re.compile(
    r"^([ \t]*<(?:h1|h2|h3|h4|h5|h6)[ \t]+(?:.*?=[^>]*?)>)"  # prefix: "<h1 id="id">""
    r"(.*?)"  # heading: "this IS a Heading"
    r"((?:<a|<\/h)(?:.*))$",  # suffix: "<a>&para;</a></h1>"
)


def ignore_word(
    ignored_casefolded_word_mapping: dict[str, str],
    word: str,
    **kwargs,  # noqa: ANN003, ARG001 | Required by titlecase callback
) -> str | None:
    """Ignore titlecasing word if present in mapping.

    Strips surrounding punctuation, then casefolds. If the stripped, casefolded
    word is present in the mapping, then the mapped value is returned rewrapped
    with its punctuation.

    If it is not present, then attempt to find the word with its surrounding
    punctuation. If present, then return the mapped value.

    If still not present, return None.

    Used as callback in titlecase(..., callback, ...).
    """
    match = PUNCTUATION_CAPTURE_RE.fullmatch(word)
    if match is None:
        raise RuntimeError

    prefix, stripped_word, suffix = match.groups()
    stripped_casefold_word = stripped_word.casefold()

    canonical_word = ignored_casefolded_word_mapping.get(stripped_casefold_word)
    if canonical_word is not None:
        return prefix + canonical_word + suffix

    full_word = prefix + stripped_casefold_word + suffix
    canonical_word = ignored_casefolded_word_mapping.get(full_word)
    if canonical_word is not None:
        return canonical_word

    return None


def parse_html_heading(line: str) -> tuple[str, str, str] | None:
    """Parse a candidate HTML heading. Return None if no match."""
    match = HTML_HEADING_RE.fullmatch(line)
    if match is not None:
        return (
            match[1],
            strip_code_tag_html(match[2]),
            match[3],
        )
    return None


def strip_code_tag_html(line: str) -> str:
    """Remove <code> and </code> tags from input."""
    line = line.strip()
    parts = _get_parts(line, r"<code>", r"</code>")
    return "".join(parts)


def _get_parts(text: str, start: str, end: str) -> list[str]:
    out: list[str] = []
    while True:
        parts = text.split(start, maxsplit=1)
        out.append(parts[0])
        if len(parts) == 1:
            break

        parts = parts[-1].split(end, maxsplit=1)
        if len(parts) == 1:
            msg = f"Missing matching: {end}"
            raise RuntimeError(msg)

        out.append(parts[0])
        text = parts[-1]

    return out
