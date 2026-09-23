import type { Brief, Script, ScriptSegment } from "../types.js";
import type { StudioConfig } from "../config.js";
import { countWords, estimateSeconds, titleCase } from "../text.js";

interface ChatCompletionResponse {
  choices?: Array<{ message?: { content?: string } }>;
}

function buildPrompt(brief: Brief): string {
  return [
    `Write a spoken-word product podcast script about "${brief.product}".`,
    `Audience: ${brief.audience}. Tone: ${brief.tone}.`,
    `Target length: about ${brief.targetSeconds} seconds when read aloud.`,
    `Cover these points: ${brief.keyPoints.join("; ")}.`,
    "",
    "Return ONLY valid JSON of the form:",
    `{"title": string, "segments": [{"role": "hook"|"point"|"bridge"|"cta", "text": string}]}`,
    "Open with a strong hook, keep sentences punchy, and finish with a clear call to action.",
  ].join("\n");
}

/**
 * Live script generation via the xAI Grok chat completions API
 * (OpenAI-compatible). Only used when an XAI_API_KEY is configured.
 */
export async function generateXaiScript(
  brief: Brief,
  config: StudioConfig,
): Promise<Script> {
  if (!config.xaiApiKey) {
    throw new Error("XAI_API_KEY is not configured");
  }

  const response = await fetch(`${config.xaiBaseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${config.xaiApiKey}`,
    },
    body: JSON.stringify({
      model: config.scriptModel,
      temperature: 0.8,
      messages: [
        {
          role: "system",
          content:
            "You are a world-class podcast scriptwriter who maximizes listener retention.",
        },
        { role: "user", content: buildPrompt(brief) },
      ],
    }),
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    throw new Error(`xAI script generation failed (${response.status}): ${detail}`);
  }

  const data = (await response.json()) as ChatCompletionResponse;
  const content = data.choices?.[0]?.message?.content?.trim();
  if (!content) {
    throw new Error("xAI returned an empty script");
  }

  const parsed = parseScriptJson(content);
  const body = parsed.segments.map((s) => s.text).join(" ");

  return {
    title: parsed.title || `${titleCase(brief.product)} Episode`,
    segments: parsed.segments,
    body,
    source: "xai",
    model: config.scriptModel,
    wordCount: countWords(body),
    estimatedSeconds: estimateSeconds(body),
  };
}

function parseScriptJson(content: string): {
  title: string;
  segments: ScriptSegment[];
} {
  const jsonStart = content.indexOf("{");
  const jsonEnd = content.lastIndexOf("}");
  const slice = jsonStart >= 0 ? content.slice(jsonStart, jsonEnd + 1) : content;
  const raw = JSON.parse(slice) as {
    title?: string;
    segments?: Array<{ role?: string; text?: string }>;
  };
  const segments: ScriptSegment[] = (raw.segments ?? [])
    .filter((s) => s.text)
    .map((s) => ({
      role: normalizeRole(s.role),
      text: String(s.text).trim(),
    }));
  if (!segments.length) {
    throw new Error("xAI script contained no segments");
  }
  return { title: raw.title?.trim() ?? "", segments };
}

function normalizeRole(role: string | undefined): ScriptSegment["role"] {
  if (role === "hook" || role === "point" || role === "bridge" || role === "cta") {
    return role;
  }
  return "point";
}
