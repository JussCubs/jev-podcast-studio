#!/usr/bin/env node
import { getConfig } from "./config.js";
import { runPipeline } from "./pipeline.js";
import type { Brief, Tone } from "./types.js";

interface CliArgs {
  [key: string]: string | undefined;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = {};
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token.startsWith("--")) {
      const key = token.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith("--")) {
        args[key] = next;
        i++;
      } else {
        args[key] = "true";
      }
    }
  }
  return args;
}

const TONES: Tone[] = ["energetic", "authoritative", "friendly", "playful"];

function bar(value: number, width = 24): string {
  const filled = Math.round((value / 100) * width);
  return "█".repeat(filled) + "░".repeat(width - filled);
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    console.log(
      [
        "jev-studio — generate a scored product podcast episode",
        "",
        "Usage:",
        '  npm run cli -- --product "Acme CLI" --audience "indie developers" \\',
        '    --points "instant setup;zero config;works offline" --tone energetic',
        "",
        "Options:",
        "  --product    Product or topic (required)",
        "  --audience   Target audience (default: builders)",
        "  --points     Semicolon-separated talking points",
        "  --tone       energetic | authoritative | friendly | playful",
        "  --seconds    Target length in seconds (default: 60)",
        "  --out        Output directory (default: ./output)",
      ].join("\n"),
    );
    return;
  }

  const config = getConfig();
  const tone = (args.tone as Tone) ?? "energetic";

  const brief: Brief = {
    product: args.product ?? "Acme Studio",
    audience: args.audience ?? "builders",
    keyPoints: (args.points ?? "it just works;it saves you time;it scales with you")
      .split(";")
      .map((p) => p.trim())
      .filter(Boolean),
    tone: TONES.includes(tone) ? tone : "energetic",
    targetSeconds: Number(args.seconds) || 60,
  };

  console.log(`\n🎙  jev-podcast-studio  (${config.liveMode ? "LIVE xAI" : "offline"} mode)\n`);
  const result = await runPipeline(brief, { outputDir: args.out });

  console.log(`Title:  ${result.script.title}`);
  console.log(
    `Script: ${result.script.wordCount} words · ~${result.script.estimatedSeconds}s · source=${result.script.source} (${result.script.model})\n`,
  );

  result.script.segments.forEach((segment) => {
    console.log(`  [${segment.role.toUpperCase()}] ${segment.text}`);
  });

  console.log(`\n── Jev Score ─────────────────────────────`);
  console.log(`  Overall: ${result.score.overall}/100  (grade ${result.score.grade})\n`);
  result.score.metrics.forEach((m) => {
    console.log(`  ${m.label.padEnd(16)} ${bar(m.score)} ${m.score}`);
  });
  console.log("");
  result.score.notes.forEach((note) => console.log(`  • ${note}`));

  console.log(`\n── Audio ─────────────────────────────────`);
  console.log(
    `  ${result.audio.path}\n  ${result.audio.format.toUpperCase()} · ${result.audio.durationSeconds}s · ${(
      result.audio.bytes / 1024
    ).toFixed(0)} KB · voice=${result.audio.voice} · source=${result.audio.source}\n`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
