import fs from "node:fs";
import path from "node:path";
import type { AudioResult, Script } from "../types.js";
import type { StudioConfig } from "../config.js";

/**
 * Live expressive text-to-speech via the xAI audio/speech endpoint
 * (OpenAI-compatible shape). Only used when an XAI_API_KEY is configured.
 * Writes an MP3 file and returns its metadata.
 */
export async function synthesizeXai(
  script: Script,
  config: StudioConfig,
  outPath: string,
): Promise<AudioResult> {
  if (!config.xaiApiKey) {
    throw new Error("XAI_API_KEY is not configured");
  }

  const response = await fetch(`${config.xaiBaseUrl}/audio/speech`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${config.xaiApiKey}`,
    },
    body: JSON.stringify({
      model: config.ttsModel,
      voice: config.ttsVoice,
      input: script.body,
      response_format: "mp3",
    }),
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`xAI TTS failed (${response.status}): ${detail}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  const audio = Buffer.from(arrayBuffer);
  const mp3Path = outPath.replace(/\.wav$/, ".mp3");
  fs.mkdirSync(path.dirname(mp3Path), { recursive: true });
  fs.writeFileSync(mp3Path, audio);

  return {
    source: "xai",
    format: "mp3",
    path: mp3Path,
    bytes: audio.length,
    durationSeconds: script.estimatedSeconds,
    voice: config.ttsVoice,
  };
}
