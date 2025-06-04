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

HTML_UNSAFE_DECODINGS = {
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
    echo_term in Term("<`", "echo", ">`") -> True
    """

    _prefix: str
    _word: str
    _suffix: str

    @property
    def word(self) -> str:
        """Return the word of this Term."""
        return self._word

    @property
    def lookup_word(self) -> str:
        """Return the word casefolded."""
        return self._word.casefold()

    @property
    def has_affixes(self) -> bool:
        """Return True if prefix or suffix are not empty."""
        return len(self._prefix) > 0 or len(self._suffix) > 0

    def __eq__(self, other: Term) -> bool:
        """Return True if words match."""
        return (
            other._prefix == self._prefix
            and other._word == self._word
            and other._suffix == self._prefix
        )

    def __hash__(self) -> int:
        """Return hash of word."""
        return hash((self._prefix, self._word, self._suffix))

    def __str__(self) -> str:
        """Return full composed representation."""
        return self._prefix + self._word + self._suffix

    def casefold(self) -> Term:
        """Create new Term with casefolded word."""
        return Term(self._prefix, self._word.casefold(), self._suffix)

    def adopt_prefix_and_suffix(self, other: Term) -> Term:
        """Create new Term with self's word and other's prefix and suffix."""
        return Term(other._prefix, self._word, other._suffix)

    def has_same_word_superset_affixes(self, other: Term) -> bool:
        """Return True is affixes in, word equal."""
        return (
            other._prefix in self._prefix
            and other._suffix in self._suffix
            and other._word == self._word
        )

    def has_same_word_subset_affixes(self, other: Term) -> bool:
        return (
            self._prefix in other._prefix
            and self._suffix in other._suffix
            and other._word == self._word
        )

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


def to_ignored_terms_mapping(lines: list[str]) -> dict[str, Term]:
    """Convert a list of string terms into a Term object mapping."""
    terms = [Term.from_string(line.strip()) for line in lines]
    return {term.lookup_word: term for term in terms}


def is_term_ignored(
    ignored_terms: dict[str, Term],
    term: str,
    **kwargs,  # noqa: ANN003, ARG001 | Required by titlecase callback
) -> str | None:
    """Ignore titlecasing word if present in mapping.

    - Will return the canonical representation of the input Term's word surrounded
      by the input Term's punctuation, or none.
    - A string is returned whenever the input word is an exact match, and the
      input term has the same set of punctuation as, or larger than, the
      canonical representation.
    - Punctuation order does not matter.
    - A string is also returned whenever the input word is a casefolded match
      and an exact punctuation match.
    - None is returned in all other cases.

    Used as callback in titlecase(..., callback, ...).
    """
    # look up duple based on just the word
    #   first is match term
    #   second is canonical term

    # then proceed to checking below

    lookup_term = Term.from_string(term)
    if lookup_term.lookup_word not in ignored_terms:
        return None

    canonical_term = ignored_terms[lookup_term.lookup_word]
    representation_term = canonical_term.adopt_prefix_and_suffix(lookup_term)

    ### EXACT WORD MATCHES
    # Exact word match, exact affix match.
    # FAQ? == FAQ? => FAQ?
    if lookup_term == canonical_term:
        return str(representation_term)

    # Exact word match, lookup affix superset canonical.
    # FAQ? > FAQ => FAQ?
    if lookup_term.has_same_word_superset_affixes(canonical_term):
        return str(representation_term)

    # Exact word match, lookup affix subset canonical.
    # FAQ < FAQ? => FAQ
    if lookup_term.has_same_word_subset_affixes(canonical_term):
        return None

    ### CASEFOLD WORD MATCHES
    casefold_lookup_term = lookup_term.casefold()
    casefold_canonical_term = canonical_term.casefold()
    # Casefold word match, exact affix match.
    if casefold_lookup_term == casefold_canonical_term:
        return str(representation_term)

    # Casefold word match, lookup affix superset canonical.
    if casefold_lookup_term.has_same_word_superset_affixes(casefold_canonical_term):
        return None

    # Casefold word match, lookup affix subset canonical.
    if casefold_lookup_term.has_same_word_subset_affixes(casefold_canonical_term):
        return None

    # Otherwise, return the canonical word wrapped with the lookup punctuation.
    representation_term = canonical_term.adopt_prefix_and_suffix(lookup_term)
    return str(representation_term)


def parse_html_heading(line: str) -> tuple[str, str, str] | None:
    """Parse a candidate HTML heading. Return None if no match."""
    match = HTML_HEADING_RE.fullmatch(line)
    if match is not None:
        heading = match[2]
        for encoded, decoded in HTML_UNSAFE_DECODINGS.items():
            heading = heading.replace(encoded, decoded)
        return (match[1], heading, match[3])
    return None
