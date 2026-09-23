---
name: podcast-perform
description: Turn a plain two-host script into an xAI-tagged performance script (pauses, laughs, cry/sigh, whisper, intensity, singing, hum-tune, laugh-speak). Use after outline/plain script and before Jev scoring or TTS render.
---

# Perform the script (heavy model)

You are the **voice director**, not the judge. Write tags into `turn.text`. Leave Jev out of the prose.

Inputs: `script.plain.json` (or beats + facts) + a preset + `docs/xai-speech-tags.md`.
Output: `script.performed.json` with `"stage": "performed"`.

## Catalog (do not omit dramatic tags)

Inline: `[pause]` `[long-pause]` `[laugh]` `[chuckle]` `[giggle]` `[cry]` `[hum-tune]` `[tsk]` `[tongue-click]` `[lip-smack]` `[breath]` `[inhale]` `[exhale]` `[sigh]`

Wrapping: `<whisper>` `<soft>` `<loud>` `<build-intensity>` `<decrease-intensity>` `<emphasis>` `<slow>` `<fast>` `<higher-pitch>` `<lower-pitch>` `<singing>` `<sing-song>` `<laugh-speak>`

Aliases the validator canonicalizes: `[hum]` → `hum-tune`, `<sing>` → `singing`, `<laugh-while-speaking>` → `laugh-speak`.

Verify against https://docs.x.ai/developers/model-capabilities/audio/text-to-speech — the list can move.

## How to tag

- Put inline tags where a person would actually make the sound. `"Really? [laugh] That's incredible!"` beats a pile of tags at the end.
- Wrap **phrases**, not single function words. `<whisper>It is a secret.</whisper>`
- Combine with punctuation. Do not STACK `[laugh][chuckle][giggle]`.
- `[pause]` / `[long-pause]` let a number or a turn land.
- `<emphasis>` for the word that must not be mumbled. Never ALL CAPS (xAI may spell those out).
- `<laugh-speak>` when they are talking through a laugh. `[laugh]` when the laugh is the event.
- `<singing>` = actually sung. `<sing-song>` = lilt. `[hum-tune]` = hummed think-pause.
- `[cry]` `[sigh]` `<decrease-intensity>` `<lower-pitch>` are the somber path. Use when the words are grief, harm, apology — not on a pricing table.

## Density by genre

Read `skills/README.md` and `rubrics/genres/<genre>.json`.

| Genre | Default density | Freely used | Earned / Jev-gated |
| --- | --- | --- | --- |
| informative | alive-sparse | pause, emphasis, chuckle, loud, breath | whisper, laugh-speak; cry/sing usually wrong |
| narrative | alive-rich | pause, long-pause, breath, whisper, intensity | cry |
| interview | alive-sparse | pause, breath, chuckle, tsk | loud, laugh |
| educational | alive-sparse | pause, emphasis, slow, tongue-click | jingle only if pedagogy |
| comedy | alive-rich | laugh, chuckle, giggle, laugh-speak | still no laugh-track SFX |
| musical | alive-rich | singing, sing-song, hum-tune | — |
| dramatic | alive-rich | cry, sigh, inhale/exhale, long-pause, decrease-intensity | giggle on grief is wrong |

If the **preset** skip-lists a tag (`roberto-agent` skip-lists cry/singing/sing-song/hum-tune), do not emit it even if the genre rubric would allow it. Change preset to `general` (or a dramatic/musical preset) instead of smuggling tags.

## Process

1. Copy plain turns. Keep `id`, `speaker`, `beat_id`.
2. For each turn, pick a delivery path from `rubrics/emotion-density.json` (`conversational`, `punchy_emphasis`, `laugh_playful`, `whisper_intimate`, `somber_cry`, `musical_sung`, `intense_build`). If you would pick `overacted_reject`, rewrite the line without extra tags.
3. Add the **fewest** tags that make that path audible.
4. Fill `text_plain` (tag-stripped). The validator will fill it if you forget.
5. Set `"stage": "performed"`.
6. `python pipeline/render_episode.py validate script.performed.json --preset <id>`

## Examples (from xAI docs)

```
So I walked in and [pause] there it was. [laugh] I honestly could not believe it!
I need to tell you something. <whisper>It is a secret.</whisper>
```

Kit examples: `examples/impact-brief/script.performed.json` (informative), `examples/genre-snippets/dramatic.performed.json`, `examples/genre-snippets/musical.performed.json`.
