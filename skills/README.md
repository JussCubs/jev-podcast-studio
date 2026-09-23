# Skills and genres

Start at [`podcast-studio/SKILL.md`](podcast-studio/SKILL.md). Child skills:

| Skill | Who | Does |
| --- | --- | --- |
| [podcast-perform](podcast-perform/SKILL.md) | Heavy model | Writes xAI speech tags into the script |
| [podcast-jev-score](podcast-jev-score/SKILL.md) | Jev | Typed Choice / Noul / Score; never dialogue |
| [podcast-render-xai](podcast-render-xai/SKILL.md) | Code + xAI + ffmpeg | Audio |

Default preset is **`general`** (full tag set). Genre picks a **rubric pack** and an **SFX density policy**. Presets may further skip-list tags (see `presets/roberto-agent.json`) without deleting them from the kit.

## Genre map

| Genre | Use it for | Rubric pack | SFX policy | Notes |
| --- | --- | --- | --- | --- |
| **informative** | Product briefs, changelog shows, "what shipped" | `rubrics/genres/informative.json` + retention + emotion + sfx | `voice-first-sparse` | Default for `roberto-agent`. Cry/sing usually wrong. |
| **narrative** | Story, scene, character | `rubrics/genres/narrative.json` | `sting-only` | Jev `somber_path_ok` before cry. |
| **interview** | Guest, debate, multi-host argument | `rubrics/genres/interview.json` | `none` | Distinct `voice_id` per person. |
| **educational** | Course module, how-to | `rubrics/genres/educational.json` | `sting-only` | Chapters from beats in `general`. |
| **comedy** | Entertainment, banter | `rubrics/genres/comedy.json` | `comedy-accents` | Denser laughs via **tags**. No laugh track. |
| **musical** | Jingle, sung interlude, hummed think | `rubrics/genres/musical.json` | `musical-beds` | `<singing>` `<sing-song>` `[hum-tune]`. |
| **dramatic** | Grief, apology, weight | `rubrics/genres/dramatic.json` | `sting-only` | `[cry]` `[sigh]` `<decrease-intensity>` are first-class. |

Set `episode.genre` to one of those enum values (`pipeline/schemas/episode.schema.json`).

## Picking tags vs SFX

Speech tags are acting. SFX is scenery. If a laugh can be `[laugh]`, do not mix a canned track. If a pause can be `[pause]`, do not whoosh. Musical beds are allowed only under the musical policy, ducked under speech.

## Adding a genre

1. Add the enum value in the episode schema and this table.
2. Drop `rubrics/genres/<id>.json` with `sfx_policy_id`, `tag_guidance`, `writer_notes`.
3. Point `presets/<show>.json` `default_genre` / `rubric_pack` at it if that show lives there.
