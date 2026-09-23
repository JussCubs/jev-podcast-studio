export type Tone = "energetic" | "authoritative" | "friendly" | "playful";

export interface Brief {
  /** Product or topic the podcast episode is about. */
  product: string;
  /** Audience the episode targets, e.g. "indie developers". */
  audience: string;
  /** Key selling points / talking points to cover. */
  keyPoints: string[];
  /** Desired delivery tone. */
  tone: Tone;
  /** Target spoken length in seconds. */
  targetSeconds: number;
}

export interface ScriptSegment {
  /** Structural role of the segment. */
  role: "hook" | "point" | "bridge" | "cta";
  /** Spoken text. */
  text: string;
}

export interface Script {
  title: string;
  segments: ScriptSegment[];
  /** Full spoken text joined from all segments. */
  body: string;
  /** Which generator produced this script. */
  source: "xai" | "offline";
  model: string;
  wordCount: number;
  estimatedSeconds: number;
}

export interface JevMetric {
  key: string;
  label: string;
  /** 0-100 sub-score. */
  score: number;
  /** Weight applied to the overall score (0-1). */
  weight: number;
  detail: string;
}

export interface JevScore {
  /** 0-100 weighted attention-holding score. */
  overall: number;
  grade: "A" | "B" | "C" | "D" | "F";
  metrics: JevMetric[];
  /** Predicted listener retention per segment (0-1). */
  retentionCurve: number[];
  notes: string[];
}

export interface AudioResult {
  source: "xai" | "offline";
  format: "wav" | "mp3";
  /** Absolute or relative path to the written audio file. */
  path: string;
  bytes: number;
  durationSeconds: number;
  voice: string;
}

export interface EpisodeResult {
  brief: Brief;
  script: Script;
  score: JevScore;
  audio: AudioResult;
  createdAt: string;
}
