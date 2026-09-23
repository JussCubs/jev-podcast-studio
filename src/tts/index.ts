import type { AudioResult, Script } from "../types.js";
import { getConfig, type StudioConfig } from "../config.js";
import { synthesizeOffline } from "./offline.js";
import { synthesizeXai } from "./xai.js";

/**
 * Synthesize speech for a script. Uses xAI expressive TTS when configured and
 * transparently falls back to the offline cadence synthesizer otherwise (or
 * when the live call fails), so the pipeline always produces audio.
 */
export async function synthesize(
  script: Script,
  outPath: string,
  config: StudioConfig = getConfig(),
): Promise<AudioResult> {
  if (config.liveMode) {
    try {
      return await synthesizeXai(script, config, outPath);
    } catch (error) {
      console.warn(
        `[tts] xAI TTS failed, using offline fallback: ${(error as Error).message}`,
      );
    }
  }
  return synthesizeOffline(script, outPath);
}

export { synthesizeOffline, synthesizeXai };
