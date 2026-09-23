import path from "node:path";
import type { Brief, EpisodeResult } from "./types.js";
import { getConfig, type StudioConfig } from "./config.js";
import { generateScript } from "./generator/index.js";
import { scoreScript } from "./scoring/jev.js";
import { synthesize } from "./tts/index.js";

export interface PipelineOptions {
  /** Directory to write audio into. */
  outputDir?: string;
  /** Base file name (without extension) for the audio artifact. */
  slug?: string;
  config?: StudioConfig;
}

function slugify(input: string): string {
  return (
    input
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60) || "episode"
  );
}

/**
 * Run the full studio pipeline for a brief:
 * generate script -> score with Jev -> synthesize expressive audio.
 */
export async function runPipeline(
  brief: Brief,
  options: PipelineOptions = {},
): Promise<EpisodeResult> {
  const config = options.config ?? getConfig();
  const outputDir = options.outputDir ?? path.resolve(process.cwd(), "output");
  const slug = options.slug ?? slugify(brief.product);
  const audioPath = path.join(outputDir, `${slug}.wav`);

  const script = await generateScript(brief, config);
  const score = scoreScript(script);
  const audio = await synthesize(script, audioPath, config);

  return {
    brief,
    script,
    score,
    audio,
    createdAt: new Date().toISOString(),
  };
}
