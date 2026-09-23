import fs from "node:fs";
import path from "node:path";
import type { AudioResult, Script } from "../types.js";
import { WORDS_PER_MINUTE, countWords, hashString } from "../text.js";
import { encodeWav } from "./wav.js";

const SAMPLE_RATE = 22050;

/**
 * Offline "voice-over" synthesizer. Real speech synthesis needs a model or a
 * network call, so when no xAI key is present we render a deterministic
 * cadence track: one soft tone burst per word, timed to a natural speaking
 * rate, with pauses at punctuation. The result is a valid, playable WAV whose
 * length and rhythm mirror the script — a real audio artifact for the pipeline.
 */
export function synthesizeOffline(script: Script, outPath: string): AudioResult {
  const words = script.body.split(/\s+/).filter(Boolean);
  const secondsPerWord = 60 / WORDS_PER_MINUTE;
  const seedBase = hashString(script.body);

  const frames: number[] = [];
  const addSilence = (seconds: number) => {
    const n = Math.floor(seconds * SAMPLE_RATE);
    for (let i = 0; i < n; i++) frames.push(0);
  };

  // Short lead-in.
  addSilence(0.25);

  words.forEach((word, index) => {
    const clean = word.replace(/[^\w']/g, "");
    const syllables = Math.max(1, Math.ceil(countWords(clean) + clean.length / 3));
    const wordSeconds = secondsPerWord * Math.min(2, Math.max(0.5, syllables / 2));
    const toneSeconds = wordSeconds * 0.7;
    const gapSeconds = wordSeconds * 0.3;

    // Pitch varies per word so the track sounds like speech cadence, not a beep.
    const freq = 150 + (hashString(word + index) % 120);
    const toneFrames = Math.floor(toneSeconds * SAMPLE_RATE);
    for (let i = 0; i < toneFrames; i++) {
      const t = i / SAMPLE_RATE;
      // Fade envelope to avoid clicks.
      const envelope = Math.sin((Math.PI * i) / toneFrames);
      const sample =
        Math.sin(2 * Math.PI * freq * t) * 0.22 * envelope +
        Math.sin(2 * Math.PI * freq * 2 * t) * 0.06 * envelope;
      frames.push(sample);
    }
    addSilence(gapSeconds);

    // Longer pause after sentence-ending punctuation.
    if (/[.!?]$/.test(word)) addSilence(0.28);
    else if (/[,;:]$/.test(word)) addSilence(0.12);

    void seedBase;
  });

  addSilence(0.3);

  const samples = Float32Array.from(frames);
  const wav = encodeWav(samples, SAMPLE_RATE);

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, wav);

  return {
    source: "offline",
    format: "wav",
    path: outPath,
    bytes: wav.length,
    durationSeconds: Number((samples.length / SAMPLE_RATE).toFixed(2)),
    voice: "jev-cadence",
  };
}
