# vs NotebookLM-class audio

NotebookLM (and cousins) are good at **turning documents into a calm two-host summary**. That is a different product than an attention-holding show.

| | NotebookLM-style | This kit |
| --- | --- | --- |
| Author | One generative pass over sources | Heavy model writes beats with a one-idea rule |
| Judge | None (or the same model) | Jev Choice/Noul/Score + **code** thresholds |
| Delivery | Even, "helpful," low risk | Speech tags: laughs, pauses, whisper, cry, sing, intensity |
| SFX | Often a light bed / none | Voice-first cap; no laugh tracks or meme whooshes |
| Customization | Style prompt | Preset (voices, allow-list, LUFS, genre pack) |
| Failure mode | Mush you cannot point at | Named rewrite (`rewrite_one_idea`, `rewrite_overacted`) |

The point is not "more funny noises." The point is **separation of powers**: the writer is allowed to be bold; a typed model says whether the boldness is credible; ffmpeg just renders.

Use NotebookLM when you want a faithful tour of a corpus. Use this kit when you want a **show** — product brief, story, debate, lesson, bit, song, or eulogy — that a person might actually finish.

Default length we optimize for is ~4–6 minutes. Longer educational/interview genres are allowed; the one-idea-per-beat rule does not go away.
