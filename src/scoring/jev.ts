import type { JevMetric, JevScore, Script } from "../types.js";
import { countWords, splitSentences } from "../text.js";

const HOOK_WORDS = [
  "stop",
  "wild",
  "surprise",
  "secret",
  "nobody",
  "everything",
  "changes",
  "wait",
  "imagine",
  "why",
  "how",
  "plot twist",
  "here's",
];

const CURIOSITY_MARKERS = [
  "but here's",
  "the reason",
  "what if",
  "here's why",
  "the payoff",
  "stay with me",
  "it gets",
  "the difference",
];

const CTA_VERBS = [
  "try",
  "go",
  "grab",
  "start",
  "build",
  "evaluate",
  "check",
  "spin",
  "report",
  "tell",
];

function clamp(value: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, value));
}

function countMatches(text: string, needles: string[]): number {
  const lower = text.toLowerCase();
  return needles.reduce(
    (acc, needle) => acc + (lower.includes(needle) ? 1 : 0),
    0,
  );
}

function scoreHook(script: Script): JevMetric {
  const hook = script.segments.find((s) => s.role === "hook")?.text ?? script.body;
  const words = countWords(hook);
  const hookHits = countMatches(hook, HOOK_WORDS);
  const hasQuestion = /\?/.test(hook);
  const lengthPenalty = words > 35 ? (words - 35) * 1.5 : 0;
  const raw = 45 + hookHits * 14 + (hasQuestion ? 12 : 0) - lengthPenalty;
  const score = clamp(raw);
  return {
    key: "hook",
    label: "Hook strength",
    score,
    weight: 0.28,
    detail:
      hookHits > 0
        ? `Opens with ${hookHits} attention trigger(s)${hasQuestion ? " and a question" : ""}.`
        : "Opening lacks strong curiosity or urgency triggers.",
  };
}

function scorePacing(script: Script): JevMetric {
  const sentences = splitSentences(script.body);
  const lengths = sentences.map((s) => countWords(s));
  const avg = lengths.reduce((a, b) => a + b, 0) / Math.max(lengths.length, 1);
  // Ideal conversational pacing is ~10-16 words per sentence.
  const distance = Math.abs(avg - 13);
  const score = clamp(100 - distance * 6);
  return {
    key: "pacing",
    label: "Pacing",
    score,
    weight: 0.2,
    detail: `Average sentence is ${avg.toFixed(1)} words (target ~13).`,
  };
}

function scoreVariety(script: Script): JevMetric {
  const lengths = splitSentences(script.body).map((s) => countWords(s));
  if (lengths.length < 2) {
    return {
      key: "variety",
      label: "Rhythm variety",
      score: 40,
      weight: 0.16,
      detail: "Too few sentences to establish rhythm.",
    };
  }
  const avg = lengths.reduce((a, b) => a + b, 0) / lengths.length;
  const variance =
    lengths.reduce((acc, l) => acc + (l - avg) ** 2, 0) / lengths.length;
  const stdev = Math.sqrt(variance);
  // Some variation keeps ears engaged; reward a healthy stdev band.
  const score = clamp(40 + stdev * 12);
  return {
    key: "variety",
    label: "Rhythm variety",
    score,
    weight: 0.16,
    detail: `Sentence-length variation (σ=${stdev.toFixed(1)}) ${
      stdev >= 3 ? "keeps the cadence dynamic" : "is a little flat"
    }.`,
  };
}

function scoreCuriosity(script: Script): JevMetric {
  const hits = countMatches(script.body, CURIOSITY_MARKERS);
  const bridges = script.segments.filter((s) => s.role === "bridge").length;
  const score = clamp(35 + hits * 12 + bridges * 8);
  return {
    key: "curiosity",
    label: "Curiosity gaps",
    score,
    weight: 0.18,
    detail: `${hits} open-loop phrase(s) and ${bridges} bridge(s) sustain momentum.`,
  };
}

function scoreCta(script: Script): JevMetric {
  const cta = script.segments.find((s) => s.role === "cta")?.text ?? "";
  const hasCta = Boolean(cta);
  const verbHits = countMatches(cta, CTA_VERBS);
  const score = clamp(hasCta ? 55 + verbHits * 18 : 20);
  return {
    key: "cta",
    label: "Call to action",
    score,
    weight: 0.18,
    detail: hasCta
      ? `Ends on an actionable ask with ${verbHits} action verb(s).`
      : "No clear call to action detected.",
  };
}

function gradeFor(overall: number): JevScore["grade"] {
  if (overall >= 88) return "A";
  if (overall >= 76) return "B";
  if (overall >= 64) return "C";
  if (overall >= 50) return "D";
  return "F";
}

/**
 * Predicted per-segment listener retention (0-1). Attention decays over time
 * but hooks, bridges, questions, and the CTA give it a lift.
 */
function retentionCurve(script: Script): number[] {
  let retention = 1;
  const curve: number[] = [];
  script.segments.forEach((segment, index) => {
    const naturalDecay = 0.04 + index * 0.006;
    retention -= naturalDecay;
    if (segment.role === "hook") retention += 0.05;
    if (segment.role === "bridge") retention += 0.03;
    if (segment.role === "cta") retention += 0.02;
    if (/\?/.test(segment.text)) retention += 0.02;
    retention = Math.max(0.35, Math.min(1, retention));
    curve.push(Number(retention.toFixed(3)));
  });
  return curve;
}

/**
 * The Jev score: a weighted 0-100 measure of how well a script will hold a
 * listener's attention, with a per-metric breakdown and retention forecast.
 */
export function scoreScript(script: Script): JevScore {
  const metrics: JevMetric[] = [
    scoreHook(script),
    scorePacing(script),
    scoreVariety(script),
    scoreCuriosity(script),
    scoreCta(script),
  ].map((metric) => ({ ...metric, score: Math.round(metric.score) }));

  const totalWeight = metrics.reduce((acc, m) => acc + m.weight, 0);
  const overall = Math.round(
    metrics.reduce((acc, m) => acc + m.score * m.weight, 0) / totalWeight,
  );

  const notes: string[] = [];
  const weakest = [...metrics].sort((a, b) => a.score - b.score)[0];
  const strongest = [...metrics].sort((a, b) => b.score - a.score)[0];
  notes.push(`Strongest lever: ${strongest.label} (${strongest.score}).`);
  if (weakest.score < 65) {
    notes.push(`Improve ${weakest.label.toLowerCase()} to lift retention.`);
  }

  return {
    overall,
    grade: gradeFor(overall),
    metrics,
    retentionCurve: retentionCurve(script),
    notes,
  };
}
