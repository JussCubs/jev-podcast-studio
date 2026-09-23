# AGENTS.md

You are producing an attention-holding podcast with this repository, not a calm document recap.

## Read in this order

1. `README.md` (positioning)
2. `skills/README.md` (genre → rubric pack + SFX policy)
3. `skills/podcast-studio/SKILL.md` (orchestrator)
4. Preset: `presets/general.json` unless the user named another (`presets/roberto-agent.json` is an example narrowing, not the default)
5. Child skills as you hit each stage:
   - `skills/podcast-perform/SKILL.md`
   - `skills/podcast-jev-score/SKILL.md`
   - `skills/podcast-render-xai/SKILL.md`

## Invariants

- Default preset is **general** (full expressive catalog ON). Never shrink `pipeline/speech_tags.json` for one brand.
- Heavy model **writes**. Jev **judges** (Choice / Noul / Score only). Code applies `jev_thresholds`.
- xAI TTS is primary (`POST https://api.x.ai/v1/tts`); tags stay in `text`. Chatterbox/Fish are fallbacks — strip or remap tags.
- Prefer speech tags over SFX. No laugh tracks, no constant beds, no meme whooshes.

## Dry-run (no secrets)

```bash
python pipeline/render_episode.py validate examples/impact-brief/script.performed.json
python pipeline/render_episode.py render examples/impact-brief/script.performed.json --dry-run --preset general
python pipeline/render_episode.py score examples/impact-brief/script.performed.json --dry-run
```

Dramatic/musical tags must remain valid on `general`:

```bash
python pipeline/render_episode.py validate examples/genre-snippets/dramatic.performed.json --preset general
python pipeline/render_episode.py validate examples/genre-snippets/musical.performed.json --preset general
```

Those two **should fail** `--preset roberto-agent` (skip-list). That is intended.

## Live

Keys in `.env` from `.env.example`. Never commit them.

```bash
python pipeline/render_episode.py render path/to/script.performed.json --out out/episode.mp3
python pipeline/render_episode.py score path/to/script.performed.json --out out/jev.json
```

If `apply_thresholds` returns rewrite actions, go back to the heavy model for **that beat**. Do not ship.

## Schema

`pipeline/schemas/episode.schema.json` — `id`, `title`, `genre`, `hosts`, `turns` are required.
