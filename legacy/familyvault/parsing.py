"""Parse 5W free-text into normalized noun lists.

Inputs are messy: "Mom and Dad", "Mary, John & Sue", "grandma's house".
The parser splits on common separators, normalizes whitespace, and dedupes
case-insensitively. It deliberately avoids NLP — predictability beats cleverness.
"""

from __future__ import annotations

import re

_SPLIT = re.compile(r"\s*(?:,|;|\band\b|&|/)\s*", flags=re.IGNORECASE)


def split_nouns(text: str) -> list[str]:
    """Split a 5W field into individual names. Preserves casing of the first
    occurrence so the user's typed form survives if it goes on to create a file."""
    if not text or not text.strip():
        return []
    parts = [p.strip() for p in _SPLIT.split(text) if p and p.strip()]
    seen: dict[str, str] = {}
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen[key] = p
    return list(seen.values())
