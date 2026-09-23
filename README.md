# jev-podcast-studio

Agent skill studio that turns a product brief into an attention-holding podcast episode:

- **Heavy-model script generation** — a structured hook → points → CTA script from a short brief.
- **Jev attention scoring** — a weighted 0–100 score with a per-lever breakdown and a predicted listener-retention curve.
- **xAI expressive TTS** — renders the script to audio.

It runs **fully offline** with deterministic fallbacks, and transparently upgrades to live [xAI](https://x.ai) Grok script generation and expressive TTS when an `XAI_API_KEY` is present.

## Quick start

```bash
npm ci
npm run serve   # web studio on http://localhost:3000
```

Open http://localhost:3000, fill in a brief, and hit **Generate episode** to get a script, a Jev score, and playable audio.

### CLI

```bash
npm run cli -- \
  --product "Acme CLI" \
  --audience "indie developers" \
  --points "instant setup;works offline;scales with you" \
  --tone energetic
```

Audio is written to `./output/<slug>.wav`. Run `npm run cli -- --help` for all options.

## Live xAI mode

```bash
cp .env.example .env
# set XAI_API_KEY (and optionally XAI_SCRIPT_MODEL / XAI_TTS_MODEL / XAI_TTS_VOICE)
```

With a key set, script generation calls the xAI Grok chat completions API and TTS
calls the xAI `audio/speech` endpoint. If a live call fails, the studio falls back
to the offline path so a run always produces output. The web header and CLI banner
show whether the studio is in **LIVE xAI** or **offline** mode.

## Architecture

```
brief ──▶ generator ──▶ script ──▶ Jev scoring ──▶ score
                          │
                          └──────▶ TTS ──▶ audio
```

| Area | Path |
| --- | --- |
| Script generation (xAI + offline) | `src/generator/` |
| Jev attention scoring | `src/scoring/jev.ts` |
| Text-to-speech (xAI + offline WAV) | `src/tts/` |
| Pipeline orchestration | `src/pipeline.ts` |
| Web studio (Express + static UI) | `src/server.ts`, `public/` |
| CLI | `src/cli.ts` |

## Scripts

| Command | Description |
| --- | --- |
| `npm run serve` | Start the web studio (tsx). |
| `npm run dev` | Start the web studio with watch reload. |
| `npm run cli -- …` | Generate an episode from the terminal. |
| `npm run build` | Compile TypeScript to `dist/`. |
| `npm start` | Run the compiled server from `dist/`. |
| `npm run typecheck` | Type-check without emitting. |
| `npm test` | Run the vitest suite. |

## License

MIT
