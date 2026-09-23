import fs from "node:fs";
import path from "node:path";

/**
 * Minimal .env loader so the studio works without extra dependencies.
 * Real environment variables always win over values in the .env file.
 */
function loadDotEnv(): void {
  const envPath = path.resolve(process.cwd(), ".env");
  if (!fs.existsSync(envPath)) return;
  const contents = fs.readFileSync(envPath, "utf8");
  for (const rawLine of contents.split("\n")) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq === -1) continue;
    const key = line.slice(0, eq).trim();
    const value = line.slice(eq + 1).trim().replace(/^["']|["']$/g, "");
    if (!(key in process.env)) process.env[key] = value;
  }
}

loadDotEnv();

export interface StudioConfig {
  xaiApiKey: string | undefined;
  xaiBaseUrl: string;
  scriptModel: string;
  ttsModel: string;
  ttsVoice: string;
  port: number;
  /** True when a live xAI key is configured. */
  liveMode: boolean;
}

export function getConfig(): StudioConfig {
  const xaiApiKey = process.env.XAI_API_KEY?.trim() || undefined;
  return {
    xaiApiKey,
    xaiBaseUrl: process.env.XAI_BASE_URL?.trim() || "https://api.x.ai/v1",
    scriptModel: process.env.XAI_SCRIPT_MODEL?.trim() || "grok-2-latest",
    ttsModel: process.env.XAI_TTS_MODEL?.trim() || "grok-tts",
    ttsVoice: process.env.XAI_TTS_VOICE?.trim() || "ember",
    port: Number(process.env.PORT) || 3000,
    liveMode: Boolean(xaiApiKey),
  };
}
