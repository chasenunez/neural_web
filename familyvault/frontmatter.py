"""Read and write Obsidian-style YAML frontmatter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_DELIM = "---"


@dataclass
class Document:
    """A markdown file split into structured frontmatter + body."""

    frontmatter: dict[str, Any]
    body: str

    def render(self) -> str:
        """Serialize to a string suitable for writing to disk."""
        fm = yaml.safe_dump(
            self.frontmatter,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ).rstrip()
        body = self.body.rstrip() + "\n" if self.body.strip() else ""
        return f"{_DELIM}\n{fm}\n{_DELIM}\n\n{body}"


def parse(text: str) -> Document:
    """Parse a markdown string. Missing frontmatter yields an empty dict."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != _DELIM:
        return Document(frontmatter={}, body=text)
    try:
        end = lines.index(_DELIM, 1)
    except ValueError:
        return Document(frontmatter={}, body=text)
    fm_text = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        # Malformed YAML — preserve the original text in the body so nothing is
        # lost, and start with an empty frontmatter. The user can repair the
        # file by hand.
        fm = {}
        body = f"<!-- frontmatter could not be parsed -->\n{fm_text}\n\n{body}"
    if not isinstance(fm, dict):
        fm = {}
    return Document(frontmatter=fm, body=body)


def read(path: Path) -> Document:
    """Read and parse a file from disk."""
    return parse(path.read_text())


def write(path: Path, doc: Document) -> None:
    """Write a Document to disk, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc.render())
