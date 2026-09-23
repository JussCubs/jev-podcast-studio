---
name: podcast-jev-score
description: Score a podcast episode or turn with OpenRouter Jev (typesafe/jev-1.13) using Choice, Noul, and Score primitives. Use to rank cold opens, judge tag density, gate cry/sung paths, pick SFX budget, and ship-vs-rewrite. Jev must not write dialogue.
---

# Jev scores. It does not write.

Jev is a System One decision model. You send `state` + typed `questions`. You get probabilities. You **do not** ask it for a better joke, a rewrite, or a rationale.

- Endpoint: `POST https://openrouter.ai/api/alpha/decisions`
- Model: `typesafe/jev-1.13` or `~typesafe/jev-latest`
- Hub: https://openrouter.ai/docs/guides/community/jev
- Kit client: `pipeline/jev_client.py`
- Kit docs: `docs/jev-decisions.md`

## Primitives

| Primitive | Field | Returns |
| --- | --- | --- |
| Choice | `type: "choice"`, `criteria: {option: description}` | `choice`, `probabilities`, `confidence` |
| Noul | `type: "noul"`, optional true/false criteria | `noul` = P(yes) |
| Score | `type: "score"`, `criteria: [level0, …]` lowest first, 2–10 | `score` (weighted), `legend`, `probabilities`, `confidence` |

## When to call

1. **Cold opens** — Choice over `cold_open_candidates`.
2. **Each performed turn** — `JevClient.score_turn` (delivery_path, densities, credibility, somber_path_ok, musical_path_ok).
3. **SFX plan** — Choice `none | sting-only | light-bed | reject_noisy`.
4. **Ship gate** — Noul `ship_episode`. Optionally Noul `rewrite_this_beat` for beat N.

Do not batch fifty unrelated questions if state would blow the 32k context. Score turns in groups of one beat.

## Code, not vibes

After the HTTP response:

```python
from pipeline.jev_client import apply_thresholds
gate = apply_thresholds(raw, preset["jev_thresholds"])
# gate["actions"] may include rewrite_overacted, rewrite_one_idea, strip_somber_tags, …
# gate["ship"] is True only if thresholds pass and no rewrite actions.
```

If `delivery_path == overacted_reject` → rewrite the turn (heavy model).
If `somber_path_ok` is below threshold and tags include cry/sigh → strip and rewrite spoken.
If `musical_path_ok` is below threshold and tags include singing/sing-song/hum-tune → strip.

Never "fix" a low noul by asking Jev to generate text.

## CLI

```bash
# Shape only, no key
python pipeline/render_episode.py score examples/impact-brief/script.performed.json --dry-run

# Live
export OPENROUTER_API_KEY=...
python pipeline/render_episode.py score examples/impact-brief/script.performed.json --out /tmp/jev.json
```

Example payload: `examples/impact-brief/jev-score.example.json`.

## State hygiene

Send the **turn text**, beat one-idea, genre, and promise. Do not dump the whole show bible. Nested JSON is fine; Jev can read fields. Keep criteria mutually exclusive on Choice. Keep Score levels ordered and descriptive — not "1–5".
