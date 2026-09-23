---
name: podcast-studio
description: Orchestrate a short attention-holding AI podcast. Heavy model writes outline + script; Jev judges (choice/noul/score); xAI TTS renders leo/ara/etc with speech tags; ffmpeg concats. Use when the user wants an AI podcast, product brief, two-host show, audio explainer, or to beat NotebookLM-flat delivery.
---

# Podcast studio (orchestrator)

Clone-and-customize skill kit. **Default preset is `general` (full expressive range on).** Narrowing presets (example: `roberto-agent`) live under `presets/` and must not shrink the catalog.

Read this file first. Then follow the child skills in order.

## Non-negotiables

1. **Heavy generative model authors.** Outline, plain script, performance tags.
2. **Jev judges.** `POST https://openrouter.ai/api/alpha/decisions` with Choice / Noul / Score only. No prose. No "write a better line."
3. **Code thresholds.** `presets/<id>.json` → `jev_thresholds`. Branch in `pipeline/jev_client.py:apply_thresholds`.
4. **xAI TTS is primary.** Speech tags stay in `text`. Chatterbox / Fish Speech are optional fallbacks and will not honor tags 1:1 — strip or remap first.
5. **Voice-first SFX.** Prefer tags over hits. See `rubrics/sfx-policy.json`.

## Invoke tomorrow

```text
1. Read AGENTS.md and skills/README.md (pick a genre).
2. Load presets/<id>.json (default general).
3. Follow this skill, then:
     skills/podcast-perform/SKILL.md
     skills/podcast-jev-score/SKILL.md
     skills/podcast-render-xai/SKILL.md
4. Dry-run without keys:
     python pipeline/render_episode.py validate path/to/script.performed.json
     python pipeline/render_episode.py render path/to/script.performed.json --dry-run
```

## Pipeline

```
brief / source material
        │
        ▼
  [heavy] outline beats (one idea each) + 2–4 cold-open candidates
        │
        ▼
  [jev]  Choice: rank cold opens
        │
        ▼
  [heavy] write script.plain.json  (episode.schema.json)
        │
        ▼
  [heavy] perform → script.performed.json   (speech tags ∩ preset allow-list)
        │
        ▼
  [jev]  per-turn Score/Noul/Choice  +  SFX budget Choice
        │
        ▼
  [code] apply_thresholds → ship or rewrite beat N
        │
        ▼
  [xai + ffmpeg] render MP3   (or --dry-run)
```

## Writer rules (heavy model)

- Open on tension, a number, a scene, or a confession. Never "in today's episode."
- One idea per beat. Land it. Leave.
- Two or more hosts unless the preset says otherwise. They must surprise or disagree once.
- Emotion is in **speech tags**, not stage directions in parentheses.
- Full tag catalog: `docs/xai-speech-tags.md` and `pipeline/speech_tags.json`.
- Dramatic (cry/sigh) and musical (sing/sing-song/hum-tune) paths are **legal in the kit**. Use them when genre + Jev `somber_path_ok` / `musical_path_ok` say so. Do not delete them because one brand is a product brief.
- Close on a sentence a listener can steal.

## Jev rules (judge)

Questions live in `rubrics/*.json`. Typical gates:

| Moment | Primitive | Why |
| --- | --- | --- |
| Cold open | Choice | Rank candidates |
| Each turn | Score density + flat/overacted + one-idea; Noul credibility; Choice delivery_path | Catch mush and tag soup |
| Cry/sung tags | Noul somber_path_ok / musical_path_ok | Classify when dramatic tags are earned |
| SFX | Choice none / sting-only / light-bed / reject_noisy | Budget |
| Ship | Noul | Rewrite beat N vs ship |

Jev docs: `docs/jev-decisions.md`. Tutorial hub: https://openrouter.ai/docs/guides/community/jev

## Schema

`pipeline/schemas/episode.schema.json`

Minimum: `id`, `title`, `genre`, `hosts[]` (`id`, `voice_id`), `turns[]` (`id`, `speaker`, `text`).

Genres: `informative` `narrative` `interview` `educational` `comedy` `musical` `dramatic`.

## Presets

| Id | Meaning |
| --- | --- |
| `general` | Default. All tags allowed. |
| `roberto-agent` | Optional. leo+ara, ≤3 SFX / 4–6 min, skip cry/sing/sing-song/hum-tune. |

Add yours: copy `presets/general.json` → `presets/<show>.json`. See `presets/README.md`.

## Stop conditions

- Validation errors (unknown tags, unmatched wraps, SFX over cap).
- `apply_thresholds` returns actions (`rewrite_one_idea`, `rewrite_overacted`, `strip_somber_tags`, …). Heavy model rewrites **that beat**, then re-score. Do not silently ship.
- Missing keys: you may still `--dry-run`. Do not invent audio.
