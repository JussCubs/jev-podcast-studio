# Presets (bring your own)

The catalog of speech tags, Jev primitives, and ffmpeg render is **general-purpose**. A preset is a narrowing (or restating) of that catalog for one show, brand, or agent.

- Default preset: [`general.json`](general.json) — full features **on**, including cry / singing / sing-song / hum-tune.
- Example narrowing: [`roberto-agent.json`](roberto-agent.json) — leo+ara, ≤3 SFX accents in 4–6 minutes, skip cry/sing/sing-song/hum-tune unless you opt in.

Do **not** delete tags from `pipeline/speech_tags.json` to fit one brand. Encode the brand as a preset.

## Fields you usually change

| Field | What it controls |
| --- | --- |
| `voices` | xAI `voice_id` (or custom clone ids) per role |
| `allowed_inline_tags` / `allowed_wrapping_tags` | Hard allow-list at validate/render time |
| `skip_tags_by_default` | Still in the kit, but the performer skill will not use them unless the beat opts in |
| `sfx.max_accents`, `sfx.policy_id`, `sfx.allow_beds` | Density + bans (laugh tracks, meme whooshes, constant beds) |
| `default_genre` + `rubric_pack` | Which Jev questions fire |
| `loudness.i_lufs` | ffmpeg `loudnorm` integrated target |
| `chapters` | Whether beats become chapter markers |
| `brand_voice` | Constraints the **heavy model** (writer) must follow |
| `jev_thresholds` | Numbers **code** branches on after Jev returns probabilities |

Schema: [`preset.schema.json`](preset.schema.json).

## Add your own

1. Copy `presets/general.json` → `presets/<your-show>.json`.
2. Set `"id"` to the filename stem (`your-show`).
3. Narrow voices, tags, SFX, LUFS, chapters, brand_voice, thresholds, rubric_pack.
4. Point the agent at it:

```bash
python pipeline/render_episode.py validate examples/impact-brief/script.performed.json --preset your-show
```

Or set `PODCAST_PRESET=your-show` in `.env`.

5. If you introduce a new genre, add `rubrics/genres/<genre>.json` and list it in `skills/README.md`.

## Precedence

1. CLI `--preset`
2. Episode JSON `"preset"` field
3. `PODCAST_PRESET` env
4. `general`

Episode-level `hosts[].voice_id` still wins over the preset default for that role.
