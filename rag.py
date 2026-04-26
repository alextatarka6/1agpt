"""
Retrieval layer.

- Plain text files  → chunk + keyword overlap (original behaviour)
- JSON lore files   → structured scoring using trigger_phrases, people,
                       aliases, tags, and keyword overlap on content fields
"""

import json
import re
from pathlib import Path
from typing import Optional

# ── plain text chunking ───────────────────────────────────────────────────────

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
TOP_K = 5


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\b\w+\b", text.lower()))


def _chunk_text(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end].strip())
        start = end - CHUNK_OVERLAP
    return [c for c in chunks if c]


# ── lore entry scoring ────────────────────────────────────────────────────────

def _score_entry(entry: dict, query: str, query_tokens: set[str]) -> int:
    score = 0
    q_lower = query.lower()

    # trigger phrases — highest signal, exact substring
    for phrase in entry.get("trigger_phrases", []):
        if phrase and phrase.lower() in q_lower:
            score += 20

    # people names
    for person in entry.get("people", []):
        if person and person.lower() in q_lower:
            score += 10

    # aliases
    for alias in entry.get("aliases", []):
        if alias and alias.lower() in q_lower:
            score += 10

    # tags
    for tag in entry.get("tags", []):
        if tag and tag.lower() in query_tokens:
            score += 5

    # keyword overlap on content fields
    content = " ".join(filter(None, [
        entry.get("enter_here", ""),
        entry.get("annotation", ""),
    ]))
    score += len(query_tokens & _tokenize(content))

    return score


def _format_entry(entry: dict) -> str:
    parts = [entry.get("enter_here", "").strip()]
    annotation = entry.get("annotation", "").strip()
    if annotation:
        parts.append(f"({annotation})")
    return " ".join(parts)


# ── unified store ─────────────────────────────────────────────────────────────

class Store:
    def __init__(self) -> None:
        self._filename: Optional[str] = None
        # text mode
        self._chunks: list[str] = []
        # lore mode
        self._entries: list[dict] = []
        self._is_lore: bool = False

    # ── loading ───────────────────────────────────────────────────────────────

    def load(self, path: str) -> int:
        p = Path(path)
        content = p.read_text(encoding="utf-8", errors="replace")
        self._filename = p.name
        return self._ingest(p.name, content)

    def load_text(self, filename: str, content: str) -> int:
        self._filename = filename
        return self._ingest(filename, content)

    def _ingest(self, filename: str, content: str) -> int:
        if filename.lower().endswith(".json"):
            try:
                data = json.loads(content)
                if isinstance(data, list) and data and "enter_here" in data[0]:
                    self._entries = [e for e in data if e.get("ready", True)]
                    self._chunks = []
                    self._is_lore = True
                    return len(self._entries)
            except (json.JSONDecodeError, KeyError):
                pass
        # fall back to plain text chunking
        self._chunks = _chunk_text(content)
        self._entries = []
        self._is_lore = False
        return len(self._chunks)

    # ── retrieval ─────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[str]:
        if self._is_lore:
            return self._retrieve_lore(query, top_k)
        return self._retrieve_text(query, top_k)

    def _retrieve_lore(self, query: str, top_k: int) -> list[str]:
        query_tokens = _tokenize(query)
        scored = [
            (_score_entry(e, query, query_tokens), e)
            for e in self._entries
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [_format_entry(e) for score, e in scored[:top_k] if score > 0]

    def _retrieve_text(self, query: str, top_k: int) -> list[str]:
        if not self._chunks:
            return []
        query_tokens = _tokenize(query)
        scored = [
            (len(query_tokens & _tokenize(chunk)), chunk)
            for chunk in self._chunks
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored[:top_k] if score > 0]

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def filename(self) -> Optional[str]:
        return self._filename

    @property
    def loaded(self) -> bool:
        return bool(self._chunks or self._entries)

    @property
    def is_lore(self) -> bool:
        return self._is_lore


store = Store()
