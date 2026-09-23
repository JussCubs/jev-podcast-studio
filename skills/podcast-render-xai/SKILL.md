---
name: podcast-render-xai
description: Render a performed episode JSON through xAI TTS (POST https://api.x.ai/v1/tts) with speech tags inline, concat turns with ffmpeg, optional SFX duck/mix, loudnorm to MP3. Use after Jev ship gate. Supports --dry-run with no API keys.
---

# Render with xAI TTS + ffmpeg

Primary renderer. Speech tags stay **inside** `text`. There is no separate style parameter.

```
POST https://api.x.ai/v1/tts
Authorization: Bearer $XAI_API_KEY
{
  "text": "So I walked in and [pause] there it was. [laugh] I honestly could not believe it!",
  "voice_id": "leo",
  "language": "en",
  "output_format": { "codec": "wav", "sample_rate": 44100 },
  "text_normalization": true,
  "replace": { "xAI": "X A I" }
}
```

Docs: https://docs.x.ai/developers/model-capabilities/audio/text-to-speech
Voices (built-in): `eve` (energetic), `ara` (warm), `rex` (confident), `sal` (balanced), `leo` (authoritative). Custom voice ids work the same field. Case-insensitive.

## CLI

```bash
# No keys: schema + tags + SFX cap + print plan
python pipeline/render_episode.py render examples/impact-brief/script.performed.json --dry-run

# Live (needs XAI_API_KEY and ffmpeg)
python pipeline/render_episode.py render examples/impact-brief/script.performed.json --out out/impact-brief.mp3
```

Each turn is synthesized separately (so leo/ara can alternate), cached under `out/.tts-cache/`, concatenated, optional SFX mixed with ducking, then `loudnorm` from the preset (`I`/`TP`/`LRA`) to MP3.

15,000 character limit per TTS request — keep turns smaller than that. If a turn is huge, split it.

## SFX mix

`sfx_plan[].file` must exist on disk for mix to include it. Missing files are skipped (voice-only). Do not commit large binaries; see `sfx/README.md`.

Policy (default `voice-first-sparse`): ≤1 cold-open hit, ≤1 key-number ding, ≤1 section whoosh, optional outro. Ban constant beds, meme whooshes, laugh tracks. Comedy/musical genres pick denser policies in `rubrics/sfx-policy.json` — still no laugh track.

## Optional fallbacks (not primary)

| Engine | When | Tags |
| --- | --- | --- |
| **xAI TTS** | Default. Expressive, tagged. | Native |
| **Chatterbox** (local) | Offline / no xAI key | Strip tags or map a subset; quality/emotion will differ |
| **Fish Speech** (local/API) | Same | Same — do not pretend `[laugh]` is understood |

If you fall back, set `hosts[].tts_provider` to `chatterbox` or `fish` and strip tags for the renderer you actually call. This repo's `render` subcommand speaks xAI only.

## ffmpeg

Required on PATH for concat / mix / loudnorm. Typical chain is in `pipeline/render_episode.py:concat_and_mix`.

Loudness defaults (`presets/general.json`): `-16` LUFS, true peak `-1.5` dBTP, LRA `11`. Change per preset (podcast apps vs YouTube vs broadcast).
