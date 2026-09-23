import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { runPipeline } from "../src/pipeline.js";
import { generateOfflineScript } from "../src/generator/offline.js";
import type { Brief } from "../src/types.js";
import type { StudioConfig } from "../src/config.js";
import { synthesizeOffline } from "../src/tts/offline.js";

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "jev-studio-test-"));

const offlineConfig: StudioConfig = {
  xaiApiKey: undefined,
  xaiBaseUrl: "https://api.x.ai/v1",
  scriptModel: "grok-2-latest",
  ttsModel: "grok-tts",
  ttsVoice: "ember",
  port: 3000,
  liveMode: false,
};

const brief: Brief = {
  product: "Acme CLI",
  audience: "indie developers",
  keyPoints: ["instant setup", "works offline"],
  tone: "friendly",
  targetSeconds: 45,
};

afterAll(() => {
  fs.rmSync(tmpDir, { recursive: true, force: true });
});

describe("runPipeline (offline)", () => {
  it("produces a script, score, and a real WAV audio file", async () => {
    const result = await runPipeline(brief, {
      outputDir: tmpDir,
      config: offlineConfig,
    });

    expect(result.script.source).toBe("offline");
    expect(result.script.segments.length).toBeGreaterThan(2);
    expect(result.score.overall).toBeGreaterThan(0);

    expect(fs.existsSync(result.audio.path)).toBe(true);
    const bytes = fs.statSync(result.audio.path).size;
    expect(bytes).toBe(result.audio.bytes);
    expect(bytes).toBeGreaterThan(1000);

    const header = fs.readFileSync(result.audio.path).subarray(0, 4).toString("ascii");
    expect(header).toBe("RIFF");
  });

  it("is deterministic for the same brief", () => {
    const a = generateOfflineScript(brief);
    const b = generateOfflineScript(brief);
    expect(a.body).toBe(b.body);
  });
});

describe("synthesizeOffline", () => {
  it("writes a valid WAV whose byte count matches metadata", () => {
    const script = generateOfflineScript(brief);
    const out = path.join(tmpDir, "unit.wav");
    const audio = synthesizeOffline(script, out);
    expect(audio.format).toBe("wav");
    expect(fs.statSync(out).size).toBe(audio.bytes);
    expect(audio.durationSeconds).toBeGreaterThan(0);
  });
});
