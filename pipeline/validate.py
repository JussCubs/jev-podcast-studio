"""Episode JSON validation: JSON Schema when jsonschema is installed, else structural checks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.paths import EPISODE_SCHEMA_PATH
from pipeline.preset import load_preset
from pipeline.speech_tags import extract, forbidden_in_text, strip_tags

GENRES = {
    "informative",
    "narrative",
    "interview",
    "educational",
    "comedy",
    "musical",
    "dramatic",
}

SFX_KINDS = {
    "cold-open-hit",
    "key-number-ding",
    "section-whoosh",
    "outro",
    "custom",
}


@dataclass
class Issue:
    path: str
    message: str
    severity: str = "error"  # error | warning


@dataclass
class ValidationResult:
    ok: bool
    issues: list[Issue] = field(default_factory=list)
    episode: dict[str, Any] = field(default_factory=dict)
    preset: dict[str, Any] = field(default_factory=dict)

    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    def raise_if_errors(self) -> None:
        errs = self.errors()
        if errs:
            blob = "\n".join(f"- {i.path}: {i.message}" for i in errs)
            raise ValueError(f"Episode failed validation:\n{blob}")


def _load_schema() -> dict[str, Any]:
    return json.loads(EPISODE_SCHEMA_PATH.read_text(encoding="utf-8"))


def _jsonschema_issues(episode: dict[str, Any]) -> list[Issue]:
    try:
        import jsonschema
    except ImportError:
        return []
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    issues: list[Issue] = []
    for err in validator.iter_errors(episode):
        path = "$" + "".join(f"[{p!r}]" if isinstance(p, int) else f".{p}" for p in err.path)
        issues.append(Issue(path=path or "$", message=err.message))
    return issues


def _structural_issues(episode: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    for key in ("id", "title", "genre", "hosts", "turns"):
        if key not in episode:
            issues.append(Issue("$", f"missing required field '{key}'"))
    genre = episode.get("genre")
    if genre is not None and genre not in GENRES:
        issues.append(Issue("$.genre", f"unknown genre '{genre}'; want {sorted(GENRES)}"))
    hosts = episode.get("hosts")
    host_ids: set[str] = set()
    if not isinstance(hosts, list) or not hosts:
        issues.append(Issue("$.hosts", "hosts must be a non-empty array"))
    else:
        for i, host in enumerate(hosts):
            if not isinstance(host, dict) or not host.get("id") or not host.get("voice_id"):
                issues.append(Issue(f"$.hosts[{i}]", "each host needs id and voice_id"))
            else:
                host_ids.add(str(host["id"]))
    turns = episode.get("turns")
    if not isinstance(turns, list) or not turns:
        issues.append(Issue("$.turns", "turns must be a non-empty array"))
    else:
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                issues.append(Issue(f"$.turns[{i}]", "turn must be an object"))
                continue
            for req in ("id", "speaker", "text"):
                if not turn.get(req):
                    issues.append(Issue(f"$.turns[{i}]", f"missing '{req}'"))
            if turn.get("speaker") and host_ids and turn["speaker"] not in host_ids:
                issues.append(
                    Issue(
                        f"$.turns[{i}].speaker",
                        f"speaker '{turn['speaker']}' is not in hosts {sorted(host_ids)}",
                    )
                )
    beat_ids = {b.get("id") for b in episode.get("beats") or [] if isinstance(b, dict)}
    if beat_ids:
        for i, turn in enumerate(episode.get("turns") or []):
            if isinstance(turn, dict) and turn.get("beat_id") and turn["beat_id"] not in beat_ids:
                issues.append(
                    Issue(f"$.turns[{i}].beat_id", f"unknown beat_id '{turn['beat_id']}'")
                )
    for i, cue in enumerate(episode.get("sfx_plan") or []):
        if not isinstance(cue, dict) or not cue.get("id") or not cue.get("kind"):
            issues.append(Issue(f"$.sfx_plan[{i}]", "each cue needs id and kind"))
        elif cue["kind"] not in SFX_KINDS:
            issues.append(Issue(f"$.sfx_plan[{i}].kind", f"unknown kind '{cue['kind']}'"))
    return issues


def _tag_issues(episode: dict[str, Any], preset: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    stage = episode.get("stage") or "performed"
    skip = preset.get("skip_tags_by_default") or []
    allowed_inline = preset.get("allowed_inline_tags") or []
    allowed_wrap = preset.get("allowed_wrapping_tags") or []
    if stage == "plain":
        for i, turn in enumerate(episode.get("turns") or []):
            if not isinstance(turn, dict):
                continue
            extracted = extract(turn.get("text") or "")
            if extracted.uses:
                issues.append(
                    Issue(
                        f"$.turns[{i}].text",
                        "stage=plain but speech tags are present; use stage=performed or strip tags",
                        severity="warning",
                    )
                )
        return issues
    for i, turn in enumerate(episode.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        text = turn.get("text") or ""
        extracted = extract(text)
        for unk in extracted.unknown:
            issues.append(Issue(f"$.turns[{i}].text", f"unknown speech tag {unk}"))
        for um in extracted.unmatched_wraps:
            issues.append(Issue(f"$.turns[{i}].text", f"unmatched wrapping tag {um}"))
        forbidden = forbidden_in_text(text, allowed_inline, allowed_wrap, skip)
        # forbidden_in_text already includes unknown/unmatched; skip duplicates
        for item in forbidden:
            if item in extracted.unknown or item in extracted.unmatched_wraps:
                continue
            issues.append(
                Issue(
                    f"$.turns[{i}].text",
                    f"tag {item} is not allowed by preset '{preset.get('id')}' "
                    f"(skip={list(skip)})",
                )
            )
        if not (turn.get("text_plain") or "").strip():
            turn["text_plain"] = strip_tags(text)
    return issues


def _sfx_budget_issues(episode: dict[str, Any], preset: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    sfx_cfg = preset.get("sfx") or {}
    max_accents = sfx_cfg.get("max_accents")
    plan = episode.get("sfx_plan") or []
    if max_accents is not None and len(plan) > int(max_accents):
        issues.append(
            Issue(
                "$.sfx_plan",
                f"{len(plan)} accents exceed preset max_accents={max_accents}",
            )
        )
    if sfx_cfg.get("allow_laugh_track") is False:
        for i, cue in enumerate(plan):
            if isinstance(cue, dict) and "laugh" in str(cue.get("file") or "").lower():
                issues.append(Issue(f"$.sfx_plan[{i}]", "laugh-track files are banned by this preset"))
    kinds = [c.get("kind") for c in plan if isinstance(c, dict)]
    for kind in ("cold-open-hit", "key-number-ding", "section-whoosh", "outro"):
        if kinds.count(kind) > 1 and (sfx_cfg.get("policy_id") or "") in {
            "voice-first-sparse",
            "sting-only",
        }:
            issues.append(Issue("$.sfx_plan", f"policy allows at most one '{kind}'"))
    return issues


def validate_episode(
    episode: dict[str, Any],
    *,
    preset_id: str | None = None,
) -> ValidationResult:
    from pipeline.preset import resolve_preset_id

    pid = resolve_preset_id(preset_id, episode)
    preset = load_preset(pid)
    issues: list[Issue] = []
    issues.extend(_jsonschema_issues(episode))
    issues.extend(_structural_issues(episode))
    # Deduplicate schema+structural on the same path+message
    seen: set[tuple[str, str]] = set()
    deduped: list[Issue] = []
    for issue in issues:
        key = (issue.path, issue.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    issues = deduped
    if not any(i.severity == "error" for i in issues):
        issues.extend(_tag_issues(episode, preset))
        issues.extend(_sfx_budget_issues(episode, preset))
    ok = not any(i.severity == "error" for i in issues)
    return ValidationResult(ok=ok, issues=issues, episode=episode, preset=preset)


def load_episode(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
