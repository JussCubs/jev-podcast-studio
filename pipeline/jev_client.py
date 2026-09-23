"""Jev via OpenRouter Decisions API.

Jev is NOT a writer. It returns Choice / Noul / Score with probabilities.
The heavy model authors; code branches on thresholds in the preset.

Docs: https://openrouter.ai/docs/guides/community/jev
Endpoint: POST https://openrouter.ai/api/alpha/decisions
Models: typesafe/jev-1.13  or  ~typesafe/jev-latest
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"

RUBRIC_ONE_IDEA = [
    "Several unrelated ideas mashed; listener cannot quote anything.",
    "Two ideas compete; landing is fuzzy.",
    "One idea with a visible tangent that could be cut.",
    "One clear idea, earned, then the hosts leave.",
    "One idea with an unforgettable landing a listener would repeat.",
]

RUBRIC_TAG_DENSITY = [
    "Barren: zero tags, dead TTS, no breath or pause. Generic audiobook mush.",
    "Stiff: one pause maybe, still sounds read.",
    "Alive-sparse: a well-placed pause, emphasis, or small laugh. Default target for informative / educational.",
    "Alive-rich: several tags that a real host would actually do. Default target for comedy, narrative peaks, dramatic scenes.",
    "Tag soup: almost every clause wrapped or punctuated. Over-acted; credibility breaks.",
]

RUBRIC_FLAT_VS_OVERACTED = [
    "Dead-flat. Could be a voicemail.",
    "Slightly stiff. Human but cautious.",
    "Naturally alive. Laughs, hmms, pauses, emphasis where a person would.",
    "Heightened but still a person you would believe in the room.",
    "Over-acted. Community-theater or parody of emotion.",
]

DELIVERY_PATH_CRITERIA = {
    "conversational": "Two people talking. Light pauses, maybe a chuckle. No performance stunt.",
    "punchy_emphasis": "A number, a verdict, or a contradiction that wants stress, loud/emphasis, or a short pause — not tears and not song.",
    "laugh_playful": "The line is actually funny or the hosts are catching each other. Laugh, chuckle, giggle, or laugh-speak belong here.",
    "whisper_intimate": "A secret, an aside, or a confidence. Whisper or soft. Not a gimmick on a public fact.",
    "somber_cry": "Grief, loss, apology, or a weight the hosts would not joke about. Cry, sigh, exhale, decrease-intensity, lower-pitch are in-bounds. Inappropriate on a cheerful changelog.",
    "musical_sung": "The beat is a hook, jingle, sung interlude, or playful sing-song disclaimer. singing, sing-song, or hum-tune belong here. Inappropriate on a straight product brief unless the source material is itself a song.",
    "intense_build": "A rising argument or reveal. build-intensity, loud, fast. Must still be one idea.",
    "overacted_reject": "Tags are stacked for their own sake, or the path fights the words (crying on a pricing table, singing a CVE).",
}

SFX_BUDGET_CRITERIA = {
    "none": "No non-speech audio. Speech tags carry everything.",
    "sting-only": "At most a cold-open hit and an outro. No ding, no whoosh.",
    "light-bed": "Sparse accents plus an optional bed that never sits under argument.",
    "reject_noisy": "Constant beds, meme whooshes, laugh tracks, or more accents than the preset cap.",
}


class JevError(RuntimeError):
    pass


@dataclass
class JevClient:
    api_key: str | None = None
    model: str | None = None
    url: str = DECISIONS_URL
    timeout_sec: float = 30.0

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = self.model or os.environ.get("JEV_MODEL") or DEFAULT_MODEL

    def available(self) -> bool:
        return bool(self.api_key)

    def decide(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise JevError(
                "OPENROUTER_API_KEY is not set. Dry-run scoring uses --dry-run; "
                "live Jev calls need a key. Jev still does not write scripts."
            )
        payload = {
            "model": self.model,
            "state": state,
            "questions": questions,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        referer = os.environ.get("OPENROUTER_HTTP_REFERER")
        title = os.environ.get("OPENROUTER_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
        req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise JevError(f"Jev HTTP {exc.code}: {detail}") from exc
        return json.loads(raw)

    def score_turn(
        self,
        *,
        episode_meta: dict[str, Any],
        turn: dict[str, Any],
        beat: dict[str, Any] | None = None,
        genre: str,
    ) -> dict[str, Any]:
        state = {
            "genre": genre,
            "episode": episode_meta,
            "beat": beat or {},
            "turn": {
                "id": turn.get("id"),
                "speaker": turn.get("speaker"),
                "text": turn.get("text"),
                "text_plain": turn.get("text_plain"),
            },
        }
        questions = {
            "delivery_path": {
                "type": "choice",
                "instructions": "Which delivery path fits this turn given genre, beat purpose, and the words themselves?",
                "criteria": DELIVERY_PATH_CRITERIA,
            },
            "tag_density": {
                "type": "score",
                "instructions": "Where does this turn sit on expressive density relative to a credible human conversation in this genre?",
                "criteria": RUBRIC_TAG_DENSITY,
            },
            "flat_vs_overacted": {
                "type": "score",
                "instructions": "Is the performance flat, naturally alive, or over-acted?",
                "criteria": RUBRIC_FLAT_VS_OVERACTED,
            },
            "one_idea_clarity": {
                "type": "score",
                "instructions": "How clearly does this turn (in its beat) carry exactly one idea?",
                "criteria": RUBRIC_ONE_IDEA,
            },
            "credibility_holds": {
                "type": "noul",
                "instructions": "Would a skeptical listener believe this speaker knows the material and is not performing a cartoon of feeling?",
                "criteria": {
                    "true": "Emotion matches the claim. Tags support the line.",
                    "false": "Unearned cry/sing/whisper, or no pulse on a line that needs one.",
                },
            },
            "somber_path_ok": {
                "type": "noul",
                "instructions": "Is a somber/cry path appropriate for this turn?",
                "criteria": {
                    "true": "Loss, harm, apology, death, or moral weight. A dry read would be dishonest.",
                    "false": "Product fact, joke, tutorial, or light banter. Cry/sigh would be unearned.",
                },
            },
            "musical_path_ok": {
                "type": "noul",
                "instructions": "Is a musical/sung path appropriate for this turn?",
                "criteria": {
                    "true": "Explicit song, jingle, hummed think-pause, or sung button the format allows.",
                    "false": "Spoken exposition. Singing it would be a bit the hosts did not agree to.",
                },
            },
        }
        return self.decide(state, questions)

    def rank_cold_opens(self, candidates: list[dict[str, Any]], *, genre: str) -> dict[str, Any]:
        criteria = {c["id"]: c.get("text") or c.get("id") for c in candidates}
        questions = {
            "cold_open_pick": {
                "type": "choice",
                "instructions": "Which cold-open will a busy listener still be in the room for after fifteen seconds?",
                "criteria": criteria,
            }
        }
        return self.decide({"genre": genre, "candidates": candidates}, questions)

    def sfx_budget(self, *, genre: str, sfx_plan: list[dict[str, Any]], preset_sfx: dict[str, Any]) -> dict[str, Any]:
        questions = {
            "sfx_budget": {
                "type": "choice",
                "instructions": "What SFX budget should this episode use, given genre and the written plan?",
                "criteria": SFX_BUDGET_CRITERIA,
            }
        }
        return self.decide(
            {"genre": genre, "sfx_plan": sfx_plan, "preset_sfx": preset_sfx},
            questions,
        )

    def gate_ship(
        self,
        *,
        episode_meta: dict[str, Any],
        rewrite_target_beat: str | None = None,
    ) -> dict[str, Any]:
        questions = {
            "ship_episode": {
                "type": "noul",
                "instructions": "Should this episode ship as-is rather than rewrite a beat?",
                "criteria": {
                    "true": "Promise is kept, beats are one-idea, delivery is alive but credible, SFX does not compete with speech.",
                    "false": "A beat is mush, over-acted, off-promise, or the SFX plan is noisy.",
                },
            }
        }
        if rewrite_target_beat:
            questions["rewrite_this_beat"] = {
                "type": "noul",
                "instructions": f"Is beat '{rewrite_target_beat}' the one that must be rewritten before ship?",
                "criteria": {
                    "true": "This beat is the failure: mush, over-acted, or off-promise.",
                    "false": "This beat is fine; failure is elsewhere or the episode can ship.",
                },
            }
        return self.decide(episode_meta, questions)


def apply_thresholds(answers: dict[str, Any], thresholds: dict[str, float]) -> dict[str, Any]:
    """Pure code. Jev does not decide ship/rewrite — thresholds do."""
    a = answers.get("answers") or answers
    actions: list[str] = []
    delivery = (a.get("delivery_path") or {}).get("choice")
    if delivery == "overacted_reject":
        actions.append("rewrite_overacted")
    cred = (a.get("credibility_holds") or {}).get("noul")
    if cred is not None and cred < thresholds.get("credibility_noul_min", 0.72):
        actions.append("rewrite_credibility")
    one = (a.get("one_idea_clarity") or {}).get("score")
    if one is not None and one < thresholds.get("one_idea_score_min", 2.2):
        actions.append("rewrite_one_idea")
    flat = (a.get("flat_vs_overacted") or {}).get("score")
    if flat is not None:
        lo = thresholds.get("delivery_score_min", 1.6)
        hi = thresholds.get("delivery_score_max", 3.3)
        if flat < lo:
            actions.append("rewrite_too_flat")
        if flat > hi:
            actions.append("rewrite_overacted")
    somber = (a.get("somber_path_ok") or {}).get("noul")
    if delivery == "somber_cry" and somber is not None and somber < thresholds.get("somber_path_noul_min", 0.7):
        actions.append("strip_somber_tags")
    musical = (a.get("musical_path_ok") or {}).get("noul")
    if delivery == "musical_sung" and musical is not None and musical < thresholds.get("musical_path_noul_min", 0.7):
        actions.append("strip_musical_tags")
    ship = (a.get("ship_episode") or {}).get("noul")
    ship_ok = ship is None or ship >= thresholds.get("ship_noul_min", 0.78)
    sfx = (a.get("sfx_budget") or {}).get("choice")
    if sfx == "reject_noisy":
        actions.append("cut_sfx")
        ship_ok = False
    return {
        "actions": sorted(set(actions)),
        "ship": ship_ok and not actions,
        "delivery_path": delivery,
        "raw": a,
    }


def write_score_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
