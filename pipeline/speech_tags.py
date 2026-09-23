"""Canonical xAI / Grok-class speech tags + aliases.

The catalog is complete (including dramatic cry/sigh and musical sing/hum-tune).
Presets may skip-list tags; they must not be deleted from this file.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable

from pipeline.paths import TAGS_PATH

INLINE_RE = re.compile(r"\[([A-Za-z0-9_-]+)\]")
WRAP_OPEN_RE = re.compile(r"<([A-Za-z0-9_-]+)>")


@dataclass(frozen=True)
class TagInfo:
    name: str
    kind: str  # inline | wrapping
    group: str
    dramatic: bool
    somber_path: bool = False
    musical_path: bool = False
    example: str = ""


@dataclass
class TagUse:
    name: str
    kind: str
    raw: str
    canonical: str


@dataclass
class ExtractedTags:
    uses: list[TagUse] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    unmatched_wraps: list[str] = field(default_factory=list)

    @property
    def canonical_names(self) -> list[str]:
        return [u.canonical for u in self.uses]


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    return json.loads(TAGS_PATH.read_text(encoding="utf-8"))


def aliases() -> dict[str, str]:
    return {k.lower(): v for k, v in load_catalog().get("aliases", {}).items()}


def all_tags() -> dict[str, TagInfo]:
    cat = load_catalog()
    out: dict[str, TagInfo] = {}
    for item in cat["inline"]:
        info = TagInfo(
            name=item["name"],
            kind="inline",
            group=item.get("group", ""),
            dramatic=bool(item.get("dramatic")),
            somber_path=bool(item.get("somber_path")),
            musical_path=bool(item.get("musical_path")),
            example=item.get("example", ""),
        )
        out[info.name] = info
    for item in cat["wrapping"]:
        info = TagInfo(
            name=item["name"],
            kind="wrapping",
            group=item.get("group", ""),
            dramatic=bool(item.get("dramatic")),
            somber_path=bool(item.get("somber_path")),
            musical_path=bool(item.get("musical_path")),
            example=item.get("example", ""),
        )
        out[info.name] = info
    return out


def canonicalize(name: str) -> str:
    key = name.strip().lower().replace("_", "-")
    mapped = aliases().get(key, key)
    return aliases().get(mapped, mapped)


def inline_names() -> set[str]:
    return {t.name for t in all_tags().values() if t.kind == "inline"}


def wrapping_names() -> set[str]:
    return {t.name for t in all_tags().values() if t.kind == "wrapping"}


def extract(text: str) -> ExtractedTags:
    """Pull inline [tag] and wrapping <tag>…</tag> uses from a performed line."""
    cat = all_tags()
    result = ExtractedTags()
    for match in INLINE_RE.finditer(text):
        raw = match.group(1)
        canon = canonicalize(raw)
        if canon in cat and cat[canon].kind == "inline":
            result.uses.append(TagUse(name=raw, kind="inline", raw=match.group(0), canonical=canon))
        else:
            result.unknown.append(match.group(0))
    for match in WRAP_OPEN_RE.finditer(text):
        raw = match.group(1)
        canon = canonicalize(raw)
        if canon in cat and cat[canon].kind == "wrapping":
            result.uses.append(TagUse(name=raw, kind="wrapping", raw=match.group(0), canonical=canon))
        else:
            result.unknown.append(match.group(0))
    stack: list[str] = []
    token_re = re.compile(r"</?([A-Za-z0-9_-]+)>")
    for match in token_re.finditer(text):
        token = match.group(0)
        name = canonicalize(match.group(1))
        if name not in wrapping_names():
            continue
        if token.startswith("</"):
            if not stack or stack[-1] != name:
                result.unmatched_wraps.append(token)
            else:
                stack.pop()
        else:
            stack.append(name)
    result.unmatched_wraps.extend(f"<{n}>" for n in stack)
    return result


def strip_tags(text: str) -> str:
    without_wraps = re.sub(r"</?[A-Za-z0-9_-]+>", "", text)
    without_inline = INLINE_RE.sub("", without_wraps)
    return re.sub(r"\s+", " ", without_inline).strip()


def count_by_canonical(text: str) -> dict[str, int]:
    extracted = extract(text)
    counts: dict[str, int] = {}
    for use in extracted.uses:
        counts[use.canonical] = counts.get(use.canonical, 0) + 1
    return counts


def forbidden_in_text(text: str, allowed_inline: Iterable[str], allowed_wrapping: Iterable[str], skip: Iterable[str]) -> list[str]:
    allowed = {canonicalize(x) for x in list(allowed_inline) + list(allowed_wrapping)}
    skipped = {canonicalize(x) for x in skip}
    extracted = extract(text)
    bad: list[str] = []
    bad.extend(extracted.unknown)
    bad.extend(extracted.unmatched_wraps)
    for use in extracted.uses:
        if use.canonical in skipped or use.canonical not in allowed:
            bad.append(f"{use.raw}->{use.canonical}")
    return bad
