# Jev decisions in this studio

Jev is TypeSafe's System One model, routed through OpenRouter. It is **not an LLM**. It does not write podcasts. It answers typed questions with probabilities so **code** can branch.

- Hub: https://openrouter.ai/docs/guides/community/jev
- HTTP: `POST https://openrouter.ai/api/alpha/decisions`
- Model: `typesafe/jev-1.13` (pin) or `~typesafe/jev-latest` (alias)
- Context: 32k input tokens (`state` + questions). Output tokens are free; you pay input.
- Client: [`pipeline/jev_client.py`](../pipeline/jev_client.py)

## Primitives

| Primitive | Question | Returns |
| --- | --- | --- |
| **Choice** | Which of these options? | `choice`, `probabilities`, `confidence` |
| **Noul** | Does this condition hold? | `noul` ∈ [0,1] = P(yes) |
| **Score** | Where on this ordered rubric? | `score` (weighted position), `legend`, `probabilities`, `confidence` |

Score criteria are an **array, lowest first**, 2–10 descriptive levels — not "rate 1–5".

Minimal request:

```json
{
  "model": "typesafe/jev-1.13",
  "state": { "genre": "informative", "turn": { "text": "…" } },
  "questions": {
    "credibility_holds": {
      "type": "noul",
      "instructions": "Would a skeptical listener believe this speaker?",
      "criteria": {
        "true": "Emotion matches the claim.",
        "false": "Unearned cry/sing, or a dead read on a line that needs a pulse."
      }
    }
  }
}
```

The endpoint is **alpha**. Keep coupling inside `JevClient` so a shape change is one file.

## What this studio asks

Defined in `rubrics/` and issued by `JevClient`:

1. **Cold open** — Choice across candidates.
2. **Turn** — Choice `delivery_path` (includes `somber_cry`, `musical_sung`, `overacted_reject`); Score `tag_density`, `flat_vs_overacted`, `one_idea_clarity`; Noul `credibility_holds`, `somber_path_ok`, `musical_path_ok`.
3. **SFX** — Choice `none | sting-only | light-bed | reject_noisy`.
4. **Ship** — Noul `ship_episode`; optional Noul `rewrite_this_beat`.

Delivery-path criteria cover the **full** expressive range on purpose. A product-brief preset does not delete `somber_cry` from Jev; it skip-lists tags and raises `somber_path_noul_min` so unearned cry never reaches TTS.

## Thresholds are code

`apply_thresholds(answers, preset["jev_thresholds"])` returns `{actions, ship, delivery_path}`. The heavy model rewrites when `actions` is non-empty. Jev never emits the rewrite.

## Two OpenRouter surfaces

| Surface | Use |
| --- | --- |
| Decisions API (`/api/alpha/decisions`) | This repo (any language, plain HTTP) |
| System One API (`/api/v1/systemone`) | Official TypeSafe SDK pointed at OpenRouter |

Same key, same billing. We use Decisions.

## Auth

`OPENROUTER_API_KEY` in `.env`. Optional `OPENROUTER_HTTP_REFERER` / `OPENROUTER_TITLE` for OpenRouter rankings. No TypeSafe account required.
