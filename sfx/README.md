# SFX (do not commit big binaries)

Voice-first. Prefer xAI speech tags over files. If you add hits, keep them tiny, loudness-normalized, and licensed.

## Policy reminder

Default (`voice-first-sparse`): at most one **cold-open hit**, one **key-number ding**, one **section whoosh**, optional **outro**. No constant beds, no meme whooshes, no laugh tracks. Comedy and musical genres have denser policies in `rubrics/sfx-policy.json` — still no laugh track.

Roberto preset further caps **total** accents at 3 per 4–6 minutes.

## What to put here

Drop local files named to match `sfx_plan[].file`, for example:

```
sfx/cold-open-hit.wav
sfx/key-number-ding.wav
sfx/section-whoosh.wav
sfx/outro.wav
```

They are gitignored (`*.wav` / `*.mp3`). Check in **this README** and maybe a `.gitkeep`, not 48 kHz beds.

## CC0 / MIT sources (start here)

- [sound-cc0](https://github.com/rxi/sound-cc0) — tiny CC0 UI/game hits you can trim into a ding.
- [Freesound](https://freesound.org/) — filter **CC0** only; download the license with the file. Search "ui click", "notification ding", "riser short", "whoosh short".
- [thisuxhq/soundkit](https://github.com/thisuxhq/soundkit) — MIT sound kit; keep only the one-shots you need.

Trim to &lt; 400 ms for dings, &lt; 800 ms for whooshes. Peak-normalize around −3 dBFS before mix; the renderer also applies `gain_db` and ducks speech.

## Mix

`pipeline/render_episode.py` delays each cue to `at_turn_id` + `offset_ms`, sidechain-compresses speech against it, mixes, then loudnorms. If `file` is missing, the cue is skipped and the episode still renders voice-only.
