import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import express from "express";
import { getConfig } from "./config.js";
import { runPipeline } from "./pipeline.js";
import type { Brief, Tone } from "./types.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// public/ sits next to src/ in dev and next to dist/ after build.
const publicDir = fs.existsSync(path.resolve(__dirname, "../public"))
  ? path.resolve(__dirname, "../public")
  : path.resolve(process.cwd(), "public");
const outputDir = path.resolve(process.cwd(), "output");

const TONES: Tone[] = ["energetic", "authoritative", "friendly", "playful"];

export function createApp(): express.Express {
  const app = express();
  app.use(express.json({ limit: "1mb" }));

  app.get("/api/health", (_req, res) => {
    const config = getConfig();
    res.json({ status: "ok", mode: config.liveMode ? "live" : "offline" });
  });

  app.post("/api/episode", async (req, res) => {
    try {
      const body = req.body ?? {};
      const tone = TONES.includes(body.tone) ? (body.tone as Tone) : "energetic";
      const brief: Brief = {
        product: String(body.product ?? "").trim() || "Acme Studio",
        audience: String(body.audience ?? "").trim() || "builders",
        keyPoints: Array.isArray(body.keyPoints)
          ? body.keyPoints.map((p: unknown) => String(p).trim()).filter(Boolean)
          : String(body.keyPoints ?? "")
              .split(";")
              .map((p) => p.trim())
              .filter(Boolean),
        tone,
        targetSeconds: Number(body.targetSeconds) || 60,
      };

      const result = await runPipeline(brief, { outputDir });
      const audioUrl = `/audio/${path.basename(result.audio.path)}`;
      res.json({ ...result, audioUrl });
    } catch (error) {
      console.error("[server] episode generation failed", error);
      res.status(500).json({ error: (error as Error).message });
    }
  });

  app.use("/audio", express.static(outputDir));
  app.use(express.static(publicDir));

  return app;
}

const isMain =
  process.argv[1] &&
  (path.resolve(process.argv[1]) === fileURLToPath(import.meta.url) ||
    process.argv[1].endsWith("server.ts") ||
    process.argv[1].endsWith("server.js"));

if (isMain) {
  const config = getConfig();
  const app = createApp();
  app.listen(config.port, () => {
    console.log(
      `\n🎙  jev-podcast-studio listening on http://localhost:${config.port}  (${
        config.liveMode ? "LIVE xAI" : "offline"
      } mode)\n`,
    );
  });
}
