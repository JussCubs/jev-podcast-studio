# jev-podcast-studio

MIT agent skills + OpenRouter Jev + xAI TTS for attention-holding AI podcasts — **bring your own preset**.

A v0 skill kit so agents can produce short two-host shows that beat generic NotebookLM mush: informative, bold, emotionally alive (laughs, hmms, pauses, emphasis, and when earned: cry, sigh, sung lines), with sparse SFX **scored by Jev** so they stay credible.

This is a **general-purpose** studio. The Roberto product-brief profile is one optional preset. It does not define the toolkit.

## Architecture in one line

**Heavy model authors → Jev judges (Choice / Noul / Score) → code thresholds → xAI TTS (tags in `text`) → ffmpeg concat / duck / loudnorm.**

Details: [`docs/architecture.md`](docs/architecture.md) · vs NotebookLM: [`docs/vs-notebooklm.md`](docs/vs-notebooklm.md)

## Tree

```
README.md
LICENSE
AGENTS.md
.env.example
skills/README.md
skills/podcast-studio/SKILL.md
skills/podcast-perform/SKILL.md
skills/podcast-jev-score/SKILL.md
skills/podcast-render-xai/SKILL.md
presets/README.md
presets/general.json              # default — full tag set ON
presets/roberto-agent.json        # optional narrowing (leo+ara, sparse SFX, skip cry/sing)
presets/preset.schema.json
rubrics/retention-short-brief.json
rubrics/emotion-density.json      # includes somber/cry + musical/sung paths
rubrics/sfx-policy.json
rubrics/genres/*.json
pipeline/render_episode.py
pipeline/jev_client.py
pipeline/speech_tags.json         # canonical Grok-class catalog
pipeline/schemas/episode.schema.json
examples/impact-brief/script.plain.json
examples/impact-brief/script.performed.json
examples/impact-brief/jev-score.example.json
examples/genre-snippets/dramatic.performed.json
examples/genre-snippets/musical.performed.json
sfx/README.md
docs/architecture.md
docs/xai-speech-tags.md
docs/jev-decisions.md
docs/vs-notebooklm.md
```

## Agent, start here

1. Read [`AGENTS.md`](AGENTS.md) and [`skills/podcast-studio/SKILL.md`](skills/podcast-studio/SKILL.md).
2. Pick a **genre** from [`skills/README.md`](skills/README.md).
3. Pick a **preset** (`general` unless you have a show file under `presets/`).
4. Dry-run (no keys):

```bash
python pipeline/render_episode.py validate examples/impact-brief/script.performed.json
python pipeline/render_episode.py render examples/impact-brief/script.performed.json --dry-run
python pipeline/render_episode.py score examples/impact-brief/script.performed.json --dry-run
```

5. Live TTS needs `XAI_API_KEY`. Live Jev needs `OPENROUTER_API_KEY`. Copy [`.env.example`](.env.example). ffmpeg on PATH for concat/mix.

```bash
python -m unittest tests.test_studio
```

## Presets

| Preset | What you get |
| --- | --- |
| `general` (default) | Every documented speech tag, including cry / singing / sing-song / hum-tune. Jev classifies when those paths are appropriate. |
| `roberto-agent` | leo+ara, 4–6 min product briefs, ≤3 SFX accents, skip cry/sing/sing-song/hum-tune by default. |

Add yours in five minutes: [`presets/README.md`](presets/README.md).

## Speech tags

Full list: [`docs/xai-speech-tags.md`](docs/xai-speech-tags.md). Verify against [xAI TTS](https://docs.x.ai/developers/model-capabilities/audio/text-to-speech).

## Jev

Jev is **not a writer**. [`docs/jev-decisions.md`](docs/jev-decisions.md) · [OpenRouter Jev hub](https://openrouter.ai/docs/guides/community/jev)

## License

MIT © 2026 Ryan Novak / JussCubs
