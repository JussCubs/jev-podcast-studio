"""xAI TTS + ffmpeg concat / optional SFX duck-mix / loudnorm → MP3.

Dry-run validates and prints the plan. Live synthesis needs XAI_API_KEY.
ffmpeg is required for concat/mix even when TTS files already exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Allow `python pipeline/render_episode.py` from repo root.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pipeline.jev_client import JevClient, JevError, apply_thresholds  # noqa: E402
from pipeline.preset import list_presets  # noqa: E402
from pipeline.speech_tags import count_by_canonical, strip_tags  # noqa: E402
from pipeline.validate import ValidationResult, load_episode, validate_episode  # noqa: E402

XAI_TTS_URL = os.environ.get("XAI_TTS_URL") or "https://api.x.ai/v1/tts"


def _print_issues(result: ValidationResult) -> None:
    for issue in result.issues:
        print(f"  [{issue.severity}] {issue.path}: {issue.message}")


def cmd_validate(args: argparse.Namespace) -> int:
    episode = load_episode(args.episode)
    result = validate_episode(episode, preset_id=getattr(args, "preset", None))
    print(f"preset: {result.preset.get('id')}")
    print(f"genre:  {episode.get('genre')}")
    print(f"turns:  {len(episode.get('turns') or [])}")
    print(f"ok:     {result.ok}")
    _print_issues(result)
    return 0 if result.ok else 1


def _estimated_seconds(episode: dict[str, Any]) -> float:
    total = 0.0
    for turn in episode.get("turns") or []:
        if turn.get("estimated_sec") is not None:
            total += float(turn["estimated_sec"])
            continue
        plain = turn.get("text_plain") or strip_tags(turn.get("text") or "")
        words = len(plain.split())
        total += words / 2.4  # ~144 wpm conversational
    return total


def _plan(episode: dict[str, Any], preset: dict[str, Any]) -> dict[str, Any]:
    hosts = {h["id"]: h for h in episode.get("hosts") or []}
    turns = []
    for turn in episode.get("turns") or []:
        host = hosts.get(turn["speaker"], {})
        turns.append(
            {
                "id": turn["id"],
                "speaker": turn["speaker"],
                "voice_id": host.get("voice_id"),
                "provider": host.get("tts_provider") or (preset.get("tts") or {}).get("provider") or "xai",
                "tag_counts": count_by_canonical(turn.get("text") or ""),
                "chars": len(turn.get("text") or ""),
                "estimated_sec": turn.get("estimated_sec"),
            }
        )
    loud = preset.get("loudness") or {}
    return {
        "preset": preset.get("id"),
        "genre": episode.get("genre"),
        "language": episode.get("language") or (preset.get("tts") or {}).get("language") or "en",
        "target_duration_sec": episode.get("target_duration_sec") or preset.get("target_duration_sec"),
        "estimated_sec": round(_estimated_seconds(episode), 1),
        "loudnorm": {
            "I": loud.get("i_lufs", -16),
            "TP": loud.get("true_peak_dbtp", -1.5),
            "LRA": loud.get("lra", 11),
        },
        "sfx_plan": episode.get("sfx_plan") or [],
        "turns": turns,
        "fallback_tts": [
            "Primary renderer is xAI TTS (POST /v1/tts) with speech tags in `text`.",
            "Optional: Chatterbox or Fish Speech for local/offline — they will not honor xAI tags 1:1; strip tags or remap first.",
        ],
    }


def cmd_plan(args: argparse.Namespace) -> int:
    episode = load_episode(args.episode)
    result = validate_episode(episode, preset_id=getattr(args, "preset", None))
    _print_issues(result)
    if not result.ok:
        return 1
    plan = _plan(result.episode, result.preset)
    print(json.dumps(plan, indent=2))
    return 0


def _tts_cache_path(cache_dir: Path, voice_id: str, text: str, language: str) -> Path:
    digest = hashlib.sha256(f"{voice_id}|{language}|{text}".encode("utf-8")).hexdigest()[:20]
    return cache_dir / f"{voice_id}_{digest}.wav"


def synthesize_xai(
    *,
    text: str,
    voice_id: str,
    language: str,
    dest: Path,
    speed: float = 1.0,
    replace: dict[str, str] | None = None,
    sample_rate: int = 44100,
) -> None:
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("XAI_API_KEY is not set. Use --dry-run to validate without keys.")
    payload: dict[str, Any] = {
        "text": text,
        "voice_id": voice_id,
        "language": language,
        "speed": speed,
        "text_normalization": True,
        "output_format": {
            "codec": "wav",
            "sample_rate": sample_rate,
        },
    }
    if replace:
        payload["replace"] = replace
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        XAI_TTS_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI TTS HTTP {exc.code}: {detail}") from exc
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(audio)


def _run_ffmpeg(argv: list[str]) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH")
    subprocess.run([ffmpeg, "-y", *argv], check=True, capture_output=True)


def concat_and_mix(
    *,
    turn_wavs: list[Path],
    sfx_plan: list[dict[str, Any]],
    turn_ids: list[str],
    out_mp3: Path,
    loudnorm: dict[str, float],
    work: Path,
) -> None:
    """Concat turns, optionally mix SFX with ducking, loudnorm to MP3."""
    list_file = work / "concat.txt"
    lines = []
    for wav in turn_wavs:
        lines.append(f"file '{wav.resolve().as_posix()}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    concat_wav = work / "concat.wav"
    _run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(concat_wav)])

    mix_wav = work / "mix.wav"
    usable = [c for c in sfx_plan if c.get("file") and Path(c["file"]).exists()]
    if not usable:
        shutil.copyfile(concat_wav, mix_wav)
    else:
        # Place each SFX at the start of its turn (plus offset_ms) using adelay + amix.
        # Approximate turn starts by probing durations.
        starts_ms: dict[str, int] = {}
        t = 0
        for turn_id, wav in zip(turn_ids, turn_wavs, strict=True):
            starts_ms[turn_id] = t
            probe = subprocess.run(
                [
                    shutil.which("ffprobe") or "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(wav),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            t += int(float(probe.stdout.strip()) * 1000)

        inputs = ["-i", str(concat_wav)]
        filters: list[str] = []
        for i, cue in enumerate(usable, start=1):
            inputs.extend(["-i", str(Path(cue["file"]))])
            delay = starts_ms.get(str(cue.get("at_turn_id") or ""), 0) + int(cue.get("offset_ms") or 0)
            gain = 10 ** (float(cue.get("gain_db") or -8) / 20)
            duck = abs(float(cue.get("duck_db") or 8))
            filters.append(f"[{i}:a]adelay={delay}|{delay},volume={gain:.4f}[s{i}]")
            # Sidechain-duck the running voice against this sting, then mix the sting back.
            filters.append(
                f"[0:a][s{i}]sidechaincompress=threshold=0.08:ratio={max(duck, 2):.1f}:attack=20:release=250[d{i}]"
            )
        # Mix original (last duck wins as approximation for v0) with all stings.
        n = 1 + len(usable)
        last_duck = f"[d{len(usable)}]" if usable else "[0:a]"
        sting_labels = "".join(f"[s{i}]" for i in range(1, len(usable) + 1))
        filters.append(
            f"{last_duck}{sting_labels}amix=inputs={n}:duration=first:dropout_transition=0:normalize=0[mix]"
        )
        _run_ffmpeg(
            [
                *inputs,
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[mix]",
                str(mix_wav),
            ]
        )

    i = loudnorm.get("I", -16)
    tp = loudnorm.get("TP", -1.5)
    lra = loudnorm.get("LRA", 11)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        [
            "-i",
            str(mix_wav),
            "-af",
            f"loudnorm=I={i}:TP={tp}:LRA={lra}",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(out_mp3),
        ]
    )


def cmd_render(args: argparse.Namespace) -> int:
    episode = load_episode(args.episode)
    result = validate_episode(episode, preset_id=getattr(args, "preset", None))
    _print_issues(result)
    if not result.ok:
        return 1
    plan = _plan(result.episode, result.preset)
    if args.dry_run:
        print("# dry-run: no TTS, no ffmpeg, no keys required")
        print(json.dumps(plan, indent=2))
        return 0
    if plan["turns"] and any(t["provider"] != "xai" for t in plan["turns"]):
        print(
            "warning: non-xAI providers are documented fallbacks only; this renderer speaks xAI. "
            "Strip or remap tags before sending to Chatterbox/Fish.",
            file=sys.stderr,
        )
    out_dir = Path(args.out_dir or "out")
    cache = out_dir / ".tts-cache"
    cache.mkdir(parents=True, exist_ok=True)
    wavs: list[Path] = []
    turn_ids: list[str] = []
    tts = result.preset.get("tts") or {}
    replace = episode.get("pronunciation") or {}
    for turn, spec in zip(episode["turns"], plan["turns"], strict=True):
        dest = _tts_cache_path(cache, spec["voice_id"], turn["text"], plan["language"])
        if not dest.exists() or args.no_cache:
            print(f"tts {spec['id']} voice={spec['voice_id']} chars={spec['chars']}")
            synthesize_xai(
                text=turn["text"],
                voice_id=spec["voice_id"],
                language=plan["language"],
                dest=dest,
                speed=float(tts.get("speed") or 1.0),
                replace=replace or None,
                sample_rate=int(tts.get("sample_rate") or 44100),
            )
        else:
            print(f"cache hit {spec['id']}")
        wavs.append(dest)
        turn_ids.append(turn["id"])
    mp3 = Path(args.out or (out_dir / f"{episode['id']}.mp3"))
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    concat_and_mix(
        turn_wavs=wavs,
        sfx_plan=episode.get("sfx_plan") or [],
        turn_ids=turn_ids,
        out_mp3=mp3,
        loudnorm=plan["loudnorm"],
        work=work,
    )
    print(f"wrote {mp3}")
    return 0


def _dry_score_stub(episode: dict[str, Any], preset: dict[str, Any]) -> dict[str, Any]:
    """Deterministic stand-in so agents can see the report shape without keys."""
    turns = []
    for turn in episode.get("turns") or []:
        turns.append(
            {
                "turn_id": turn["id"],
                "dry_run": True,
                "note": "Live Jev was not called. Wire OPENROUTER_API_KEY for typed probabilities.",
                "expected_questions": [
                    "delivery_path (choice)",
                    "tag_density (score)",
                    "flat_vs_overacted (score)",
                    "one_idea_clarity (score)",
                    "credibility_holds (noul)",
                    "somber_path_ok (noul)",
                    "musical_path_ok (noul)",
                ],
            }
        )
    return {
        "preset": preset.get("id"),
        "model": os.environ.get("JEV_MODEL") or "typesafe/jev-1.13",
        "dry_run": True,
        "thresholds": preset.get("jev_thresholds"),
        "turns": turns,
        "sfx_budget_question": "choice none | sting-only | light-bed | reject_noisy",
        "ship_question": "noul ship_episode",
    }


def cmd_score(args: argparse.Namespace) -> int:
    episode = load_episode(args.episode)
    result = validate_episode(episode, preset_id=getattr(args, "preset", None))
    _print_issues(result)
    if not result.ok:
        return 1
    if args.dry_run or not os.environ.get("OPENROUTER_API_KEY"):
        report = _dry_score_stub(result.episode, result.preset)
        print(json.dumps(report, indent=2))
        if args.out:
            Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 0
    client = JevClient()
    beats = {b["id"]: b for b in (episode.get("beats") or []) if "id" in b}
    meta = {
        "id": episode.get("id"),
        "title": episode.get("title"),
        "genre": episode.get("genre"),
        "one_sentence_promise": episode.get("one_sentence_promise"),
    }
    turn_reports = []
    actions_all: list[str] = []
    try:
        for turn in episode["turns"]:
            raw = client.score_turn(
                episode_meta=meta,
                turn=turn,
                beat=beats.get(turn.get("beat_id")),
                genre=episode["genre"],
            )
            gated = apply_thresholds(raw, result.preset.get("jev_thresholds") or {})
            actions_all.extend(gated["actions"])
            turn_reports.append({"turn_id": turn["id"], "gate": gated, "answers": raw.get("answers")})
        sfx = client.sfx_budget(
            genre=episode["genre"],
            sfx_plan=episode.get("sfx_plan") or [],
            preset_sfx=result.preset.get("sfx") or {},
        )
        ship = client.gate_ship(episode_meta={**meta, "turn_gates": [t["gate"] for t in turn_reports]})
    except JevError as exc:
        print(f"jev error: {exc}", file=sys.stderr)
        return 1
    report = {
        "preset": result.preset.get("id"),
        "model": client.model,
        "dry_run": False,
        "thresholds": result.preset.get("jev_thresholds"),
        "turns": turn_reports,
        "sfx": sfx.get("answers"),
        "ship": ship.get("answers"),
        "actions": sorted(set(actions_all)),
    }
    print(json.dumps(report, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pipeline/render_episode.py",
        description="Validate, Jev-score, and render a podcast episode JSON. Dry-run needs no API keys.",
    )
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--preset",
        help="Preset id (default: episode.preset or PODCAST_PRESET or general)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", parents=[parent], help="Schema + tag + SFX budget checks")
    v.add_argument("episode", type=Path)
    v.set_defaults(func=cmd_validate)

    pl = sub.add_parser("plan", parents=[parent], help="Print the render plan after validation")
    pl.add_argument("episode", type=Path)
    pl.set_defaults(func=cmd_plan)

    r = sub.add_parser("render", parents=[parent], help="TTS each turn, concat, optional SFX, loudnorm MP3")
    r.add_argument("episode", type=Path)
    r.add_argument("--dry-run", action="store_true", help="Validate and print plan; no keys, no audio")
    r.add_argument("--out", type=Path, help="Output mp3 path")
    r.add_argument("--out-dir", type=Path, default=Path("out"))
    r.add_argument("--no-cache", action="store_true")
    r.set_defaults(func=cmd_render)

    s = sub.add_parser("score", parents=[parent], help="Ask Jev to judge (not write) the episode")
    s.add_argument("episode", type=Path)
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--out", type=Path)
    s.set_defaults(func=cmd_score)

    ls = sub.add_parser("presets", help="List preset ids")
    ls.set_defaults(func=lambda _a: (print("\n".join(list_presets())) or 0))
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Re-bind preset resolution after parse for subcommands that have episode.
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
