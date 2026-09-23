import type { Brief, Script } from "../types.js";
import { getConfig, type StudioConfig } from "../config.js";
import { generateOfflineScript } from "./offline.js";
import { generateXaiScript } from "./xai.js";

/**
 * Generate a podcast script from a brief. Uses the live xAI heavy model when an
 * API key is configured, and transparently falls back to the deterministic
 * offline generator otherwise (or when the live call fails).
 */
export async function generateScript(
  brief: Brief,
  config: StudioConfig = getConfig(),
): Promise<Script> {
  if (config.liveMode) {
    try {
      return await generateXaiScript(brief, config);
    } catch (error) {
      console.warn(
        `[generator] xAI generation failed, using offline fallback: ${(error as Error).message}`,
      );
    }
  }
  return generateOfflineScript(brief);
}

export { generateOfflineScript, generateXaiScript };
