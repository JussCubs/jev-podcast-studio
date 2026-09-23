# xAI / Grok-class speech tags

Inline tags produce a sound at a point in the line. Wrapping tags change how a **phrase** is delivered. They go in the TTS `text` field. There is no parallel style API.

**Verify before shipping a new tag name:** [Text to Speech](https://docs.x.ai/developers/model-capabilities/audio/text-to-speech) (current). Older bookmarks such as `https://docs.x.ai/docs/models/voice/tts` may redirect or 404 as the docs move.

Machine catalog used by the validator: [`pipeline/speech_tags.json`](../pipeline/speech_tags.json).

This kit documents the **full** expressive range, including dramatic and musical tags. Presets may skip-list names. They must not be dropped from this page.

## Inline `[tag]`

| Tag | Group | Dramatic / path | Example |
| --- | --- | --- | --- |
| `[pause]` | pauses | | So I walked in and `[pause]` there it was. |
| `[long-pause]` | pauses | dramatic timing | And then `[long-pause]` nothing. |
| `[laugh]` | laughter & crying | | `[laugh]` I honestly could not believe it! |
| `[chuckle]` | laughter & crying | | `[chuckle]` We've all been in that room. |
| `[giggle]` | laughter & crying | | Don't `[giggle]` start. |
| `[cry]` | laughter & crying | **somber/cry path** | I didn't expect it to land like that. `[cry]` |
| `[hum-tune]` | musical | **musical/sung path** | Give me a second. `[hum-tune]` Okay. Back. |
| `[tsk]` | mouth | | `[tsk]` That's the wrong number. |
| `[tongue-click]` | mouth | | `[tongue-click]` Next slide. |
| `[lip-smack]` | mouth | | `[lip-smack]` Alright. Here is the spicy bit. |
| `[breath]` | breathing | | `[breath]` Okay. One idea. |
| `[inhale]` | breathing | | `[inhale]` This is the part I wanted to get right. |
| `[exhale]` | breathing | somber-adjacent | `[exhale]` Yeah. That's the tradeoff. |
| `[sigh]` | breathing | **somber/cry path** | `[sigh]` We shipped it anyway. |

Alias: `[hum]` canonicalizes to `[hum-tune]`.

## Wrapping `<tag>…</tag>`

| Tag | Group | Path | Example |
| --- | --- | --- | --- |
| `<whisper>` | vocal style | intimate | I need to tell you something. `<whisper>`It is a secret.`</whisper>` |
| `<soft>` | volume | | `<soft>`Stay with me for this next number.`</soft>` |
| `<loud>` | volume | | `<loud>`Three million events. Not three thousand.`</loud>` |
| `<build-intensity>` | intensity | rising | `<build-intensity>`And it kept growing. And growing. And then it broke.`</build-intensity>` |
| `<decrease-intensity>` | intensity | **somber** | `<decrease-intensity>`That's the last thing she said.`</decrease-intensity>` |
| `<emphasis>` | vocal style | | The constraint is `<emphasis>`four minutes`</emphasis>`, not forty. |
| `<slow>` | speed | | `<slow>`Read the number again.`</slow>` |
| `<fast>` | speed | | `<fast>`Ship it, measure it, kill it if it lies.`</fast>` |
| `<higher-pitch>` | pitch | | `<higher-pitch>`Wait, it actually worked?`</higher-pitch>` |
| `<lower-pitch>` | pitch | dramatic | `<lower-pitch>`This is the part we do not joke about.`</lower-pitch>` |
| `<singing>` | musical | **sung** | `<singing>`Don't bury the lede.`</singing>` |
| `<sing-song>` | musical | **sung lilt** | `<sing-song>`Here comes the disclaimer.`</sing-song>` |
| `<laugh-speak>` | vocal style | talk-through-laugh | `<laugh-speak>`We did put the graph in the appendix. Once.`</laugh-speak>` |

Aliases: `<sing>` → `singing`; `<laugh-while-speaking>` → `laugh-speak`.

Official xAI examples (as of the REST voice reference):

```
So I walked in and [pause] there it was. [laugh] I honestly could not believe it!
I need to tell you something. <whisper>It is a secret.</whisper>
```

## Tips (from xAI docs)

- Place inline tags where the expression would naturally occur.
- Combine tags with punctuation rather than stacking them.
- Use `[pause]` / `[long-pause]` to let a thought land.
- Wrap complete phrases, not isolated function words.
- Do not shout in ALL CAPS; xAI may spell letters. Use `<emphasis>` or `<loud>`.

## Not native xAI

Some stacks (e.g. LiveKit `expr`) use intermediate emotion labels (`happy`, `sad`, `angry`, …). Those are **not** xAI tags. Lower them to the wrapping/inline names above before `POST /v1/tts`.

## Built-in voices

| `voice_id` | Tone (vendor description) |
| --- | --- |
| `eve` | Energetic, upbeat (TTS default if you omit `voice_id`) |
| `ara` | Warm, friendly |
| `rex` | Confident, clear |
| `sal` | Smooth, balanced |
| `leo` | Authoritative, strong |

This studio's `general` preset maps host→`leo`, cohost→`ara`. Custom clones use the same `voice_id` field.

## Request extras worth knowing

- `language` is required (`en`, `auto`, …).
- `replace`: pronunciation map, billed on the original text.
- `with_timestamps`: JSON envelope with per-character times (captions / karaoke).
- `speed`: 0.7–1.5.
- Max `text` length: 15,000 characters per request.
