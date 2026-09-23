import { describe, expect, it } from "vitest";
import { scoreScript } from "../src/scoring/jev.js";
import { generateOfflineScript } from "../src/generator/offline.js";
import type { Brief, Script } from "../src/types.js";

const brief: Brief = {
  product: "Acme CLI",
  audience: "indie developers",
  keyPoints: ["instant setup", "works offline", "scales with you"],
  tone: "energetic",
  targetSeconds: 60,
};

describe("scoreScript", () => {
  it("returns a bounded overall score and matching grade", () => {
    const script = generateOfflineScript(brief);
    const score = scoreScript(script);

    expect(score.overall).toBeGreaterThanOrEqual(0);
    expect(score.overall).toBeLessThanOrEqual(100);
    expect(["A", "B", "C", "D", "F"]).toContain(score.grade);
  });

  it("produces one metric per lever with bounded sub-scores", () => {
    const score = scoreScript(generateOfflineScript(brief));
    const keys = score.metrics.map((m) => m.key).sort();
    expect(keys).toEqual(["cta", "curiosity", "hook", "pacing", "variety"]);
    for (const metric of score.metrics) {
      expect(metric.score).toBeGreaterThanOrEqual(0);
      expect(metric.score).toBeLessThanOrEqual(100);
    }
  });

  it("emits a retention point per segment, all within [0.35, 1]", () => {
    const script = generateOfflineScript(brief);
    const score = scoreScript(script);
    expect(score.retentionCurve).toHaveLength(script.segments.length);
    for (const point of score.retentionCurve) {
      expect(point).toBeGreaterThanOrEqual(0.35);
      expect(point).toBeLessThanOrEqual(1);
    }
  });

  it("rewards a strong hook over a flat one", () => {
    const flat: Script = {
      title: "Flat",
      segments: [
        { role: "hook", text: "This is a product. It does things for people." },
        { role: "cta", text: "It exists." },
      ],
      body: "This is a product. It does things for people. It exists.",
      source: "offline",
      model: "test",
      wordCount: 11,
      estimatedSeconds: 5,
    };
    const strong = scoreScript(generateOfflineScript(brief));
    const weak = scoreScript(flat);
    const strongHook = strong.metrics.find((m) => m.key === "hook")!.score;
    const weakHook = weak.metrics.find((m) => m.key === "hook")!.score;
    expect(strongHook).toBeGreaterThan(weakHook);
  });
});
