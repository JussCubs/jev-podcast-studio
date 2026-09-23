# Architecture

```
                    ┌──────────────────────────┐
   source brief ──► │ Heavy model (Opus/Grok/…)│  outline + plain script + tags
                    └────────────┬─────────────┘
                                 │ episode JSON
                                 ▼
                    ┌──────────────────────────┐
                    │ Jev (OpenRouter Decisions)│  Choice / Noul / Score
                    └────────────┬─────────────┘
                                 │ probabilities
                                 ▼
                    ┌──────────────────────────┐
                    │ Code thresholds (preset) │  ship or rewrite beat N
                    └────────────┬─────────────┘
                                 │ performed JSON
                                 ▼
                    ┌──────────────────────────┐
                    │ xAI TTS  POST /v1/tts    │  tags stay in `text`
                    └────────────┬─────────────┘
                                 │ per-turn wav
                                 ▼
                    ┌──────────────────────────┐
                    │ ffmpeg concat + duck SFX │  loudnorm → MP3
                    │   + optional fallbacks   │  Chatterbox / Fish (strip tags)
                    └──────────────────────────┘
```

This is a **general-purpose** studio. The Roberto product-brief show is `presets/roberto-agent.json`, not the architecture.

## Layers

| Layer | Allowed to do | Forbidden |
| --- | --- | --- |
| Heavy model | Research, outline, write, tag | Grade itself; invent Jev probabilities |
| Jev | Typed decisions + probabilities | Dialogue, rationales, "improved" lines |
| Code | Schema, allow-lists, thresholds, HTTP, ffmpeg | Creative writing |
| Preset | Narrow voices, tags, SFX, LUFS, chapters | Delete tags from `pipeline/speech_tags.json` |

## Data

- Episode: `pipeline/schemas/episode.schema.json`
- Tags: `pipeline/speech_tags.json` (full Grok-class set, including dramatic + musical)
- Presets: `presets/*.json` (default `general`)
- Rubrics: `rubrics/` (Jev question text + genre packs)

## Runtime

- Python 3.11+
- `python pipeline/render_episode.py … --dry-run` — no API keys
- Live TTS: `XAI_API_KEY`
- Live Jev: `OPENROUTER_API_KEY`
- `ffmpeg` (+ `ffprobe`) for concat/mix/loudnorm

## Why this beats a single-model "make a podcast" button

NotebookLM-class tools generate calm summary audio. This kit **separates** authoring from judging, forces one-idea beats, and puts expression in the TTS stream. See `docs/vs-notebooklm.md`.
