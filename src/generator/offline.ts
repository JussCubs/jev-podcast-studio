import type { Brief, Script, ScriptSegment, Tone } from "../types.js";
import {
  countWords,
  estimateSeconds,
  hashString,
  seededRandom,
  titleCase,
} from "../text.js";

const TONE_OPENERS: Record<Tone, string[]> = {
  energetic: [
    "Okay, stop what you're doing, because this changes everything.",
    "Here's the thing nobody tells you, and it's kind of wild.",
    "I have got to talk about this, because it genuinely surprised me.",
  ],
  authoritative: [
    "Let's be precise about what actually moves the needle here.",
    "There's a lot of noise in this space, so let's cut straight to what matters.",
    "If you only remember one thing from this episode, make it this.",
  ],
  friendly: [
    "So a friend asked me about this the other day, and I loved the answer.",
    "Grab a coffee, because I want to walk you through something good.",
    "You know that feeling when a tool just gets out of your way? Yeah, this.",
  ],
  playful: [
    "Plot twist: the boring-sounding thing is secretly the fun part.",
    "Buckle up, this is the good kind of rabbit hole.",
    "I promise this is more exciting than it has any right to be.",
  ],
};

const BRIDGES = [
  "But here's where it gets interesting.",
  "Now, stay with me for a second.",
  "And that leads to the part I actually care about.",
  "So what does that mean for you?",
  "Here's the payoff.",
];

const CTA_TEMPLATES: Record<Tone, string> = {
  energetic: "If that got you fired up, go try {product} today and tell me what you build.",
  authoritative: "The move is simple: evaluate {product} against your current workflow this week.",
  friendly: "Give {product} a spin when you get a minute — I think you'll like it.",
  playful: "Go poke at {product} and see how far you can push it. Report back.",
};

function pick<T>(items: T[], rand: () => number): T {
  return items[Math.floor(rand() * items.length)];
}

function pointSentence(point: string, audience: string, rand: () => number): string {
  const frames = [
    `For ${audience}, ${lowerFirst(point)} is the difference between shipping and stalling.`,
    `${titleCase(point)}. That's not a nice-to-have, that's the whole point.`,
    `Think about ${lowerFirst(point)} — it quietly saves you hours every single week.`,
    `The reason ${audience} keep coming back? ${titleCase(point)}.`,
  ];
  return pick(frames, rand);
}

function lowerFirst(s: string): string {
  return s ? s[0].toLowerCase() + s.slice(1) : s;
}

/**
 * Deterministic, fully offline script generator. Produces a structured,
 * attention-oriented product podcast script from a brief without any network
 * call, so the studio always has a working generation path.
 */
export function generateOfflineScript(brief: Brief): Script {
  const seed = hashString(
    `${brief.product}|${brief.audience}|${brief.tone}|${brief.keyPoints.join(",")}`,
  );
  const rand = seededRandom(seed);

  const segments: ScriptSegment[] = [];

  const hook = `${pick(TONE_OPENERS[brief.tone], rand)} Today it's all about ${brief.product} — and why ${brief.audience} should care.`;
  segments.push({ role: "hook", text: hook });

  const points = brief.keyPoints.length
    ? brief.keyPoints
    : ["it just works", "it saves you time", "it scales with you"];

  points.forEach((point, index) => {
    if (index > 0) {
      segments.push({ role: "bridge", text: pick(BRIDGES, rand) });
    }
    segments.push({ role: "point", text: pointSentence(point, brief.audience, rand) });
  });

  const cta = CTA_TEMPLATES[brief.tone].replace("{product}", brief.product);
  segments.push({ role: "cta", text: cta });

  const body = segments.map((s) => s.text).join(" ");
  const wordCount = countWords(body);

  return {
    title: `${titleCase(brief.product)}: ${titleCase(brief.tone)} Rundown`,
    segments,
    body,
    source: "offline",
    model: "jev-offline-v1",
    wordCount,
    estimatedSeconds: estimateSeconds(body),
  };
}
