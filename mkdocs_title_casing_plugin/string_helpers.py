"""Helpers for string operations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self

PUNCTUATION = r"""!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_`{|}~"""  # noqa: RUF001
PUNCTUATION_CAPTURE_RE = re.compile(rf"([{PUNCTUATION}]*)(.*?)([{PUNCTUATION}]*)")
HTML_HEADING_RE = re.compile(
    r"^([ \t]*<(?:h1|h2|h3|h4|h5|h6)[ \t]+(?:.*?=[^>]*?)>)"  # prefix: "<h1 id="id">""
    r"(.*?)"  # heading: "this IS a Heading"
    r"((?:<a|<\/h)(?:.*))$",  # suffix: "<a>&para;</a></h1>"
)


def ignore_term(
    ignored_terms: dict[Term, Term],
    term: str,
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
    lookup_term = Term.from_string(term).to_lookup_form()
    if lookup_term in ignored_terms:
        ignored_term = ignored_terms[lookup_term]

        # If the exact canonical representation is not a subset of the lookup,
        # then we're out. See Term.__contains__().
        if ignored_term not in lookup_term:
            return None

        # Otherwise, return the canonical word wrapped with the lookup punctuation.
        representation_term = ignored_term.adopt_prefix_and_suffix(lookup_term)
        return str(representation_term)

    return None


HTML_UNSAFE_REPLACEMENTS = {
    "&amp;": "&",
    "&quot;": '"',
    "&#039;": "'",
    "&lt;": "<",
    "&gt;": ">",
    "&#96;": "`",
    "<code>": "`",
    "</code>": "`",
}


@dataclass(unsafe_hash=False, frozen=True)
class Term:
    """Class representing a word together with its wrapping punctuation.

    Term.from_string("`Echo`") -> Term("`", "Echo", "`")
    echo_term == echo_no_punctuation_term
    hash(echo_term) -> hash("Echo")
    str(echo_term) -> "`Echo`"
    echo_term.to_lookup_form() -> Term("`", "echo", "`")
    echo_term.adopt_prefix_and_suffix(Term("<", _, ">")) -> Term("<", "Echo", ">")
    echo_no_punctuation_term in echo_term -> True
    echo_term in echo_no_punctuation_term -> False
    echo_term in Term("<`", "echo", "`>") -> True
    """

    _prefix: str
    _word: str
    _suffix: str

    @property
    def word(self) -> str:
        """Return the word of this Term."""
        return self._word

    def __contains__(self, other: Term) -> bool:
        """Return True if parts of other are in corresponding parts of self.

        `echo` in (`echo`) -> True
        `echo` in `(echo)` -> True
        `echo` in   echo   -> False
        `echo` in   Echo   -> False

        """
        return (
            other._prefix in self._prefix
            and other.word in self.word
            and other._suffix in self._suffix
        )

    def __eq__(self, other: Term) -> bool:
        """Return True if words match."""
        return other.word == self.word

    def __hash__(self) -> int:
        """Return hash of word."""
        return hash(self.word)

    def __str__(self) -> str:
        """Return full composed representation."""
        return self._prefix + self._word + self._suffix

    def to_lookup_form(self) -> Term:
        """Create new Term with casefolded word."""
        return Term(self._prefix, self._word.casefold(), self._suffix)

    def adopt_prefix_and_suffix(self, other: Term) -> Term:
        """Create new Term with self's word and other's prefix and suffix."""
        return Term(other._prefix, self._word, other._suffix)

    @classmethod
    def from_string(cls, term: str) -> Self:
        """Create new Term given a string representation of a Term."""
        return cls(*(cls._split_punctuation(term)))

    @staticmethod
    def _split_punctuation(word: str) -> tuple[str, str, str]:
        match = PUNCTUATION_CAPTURE_RE.fullmatch(word)
        if match is None:
            raise RuntimeError

        prefix, stripped_word, suffix = match.groups()
        return (prefix, stripped_word, suffix)


def parse_html_heading(line: str) -> tuple[str, str, str] | None:
    """Parse a candidate HTML heading. Return None if no match."""
    match = HTML_HEADING_RE.fullmatch(line)
    if match is not None:
        heading = match[2]
        for encoded, decoded in HTML_UNSAFE_REPLACEMENTS.items():
            heading = heading.replace(encoded, decoded)
        return (match[1], heading, match[3])
    return None
