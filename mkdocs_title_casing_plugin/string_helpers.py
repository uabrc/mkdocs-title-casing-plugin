"""Helpers for string operations."""


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
