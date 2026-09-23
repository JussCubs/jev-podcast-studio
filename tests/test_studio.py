#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.jev_client import apply_thresholds
from pipeline.preset import list_presets, load_preset
from pipeline.speech_tags import canonicalize, extract, strip_tags
from pipeline.validate import load_episode, validate_episode


class TagTests(unittest.TestCase):
    def test_catalog_includes_dramatic_and_musical(self) -> None:
        from pipeline.speech_tags import all_tags

        names = set(all_tags())
        for required in (
            "cry",
            "sigh",
            "hum-tune",
            "singing",
            "sing-song",
            "laugh-speak",
            "build-intensity",
            "decrease-intensity",
            "whisper",
            "emphasis",
        ):
            self.assertIn(required, names)

    def test_aliases(self) -> None:
        self.assertEqual(canonicalize("hum"), "hum-tune")
        self.assertEqual(canonicalize("sing"), "singing")
        self.assertEqual(canonicalize("laugh-while-speaking"), "laugh-speak")

    def test_extract_inline_and_wrap(self) -> None:
        text = "So I walked in and [pause] there it was. [laugh] <whisper>It is a secret.</whisper>"
        got = extract(text)
        self.assertEqual(got.canonical_names, ["pause", "laugh", "whisper"])
        self.assertFalse(got.unknown)
        self.assertFalse(got.unmatched_wraps)
        self.assertEqual(strip_tags(text), "So I walked in and there it was. It is a secret.")

    def test_nested_wraps(self) -> None:
        text = "<decrease-intensity><lower-pitch>Yeah.</lower-pitch></decrease-intensity>"
        got = extract(text)
        self.assertEqual(sorted(got.canonical_names), ["decrease-intensity", "lower-pitch"])
        self.assertFalse(got.unmatched_wraps)


class PresetTests(unittest.TestCase):
    def test_general_allows_cry(self) -> None:
        g = load_preset("general")
        self.assertIn("cry", g["allowed_inline_tags"])
        self.assertIn("singing", g["allowed_wrapping_tags"])
        self.assertEqual(g["skip_tags_by_default"], [])

    def test_roberto_skips_dramatic_musical(self) -> None:
        r = load_preset("roberto-agent")
        skip = set(r["skip_tags_by_default"])
        self.assertTrue({"cry", "singing", "sing-song", "hum-tune"} <= skip)
        self.assertEqual(r["sfx"]["max_accents"], 3)
        self.assertEqual(r["voices"]["host"], "leo")
        self.assertEqual(r["voices"]["cohost"], "ara")

    def test_list_presets(self) -> None:
        ids = list_presets()
        self.assertIn("general", ids)
        self.assertIn("roberto-agent", ids)


class ValidateExamplesTests(unittest.TestCase):
    def test_plain_and_performed_general(self) -> None:
        for rel in (
            "examples/impact-brief/script.plain.json",
            "examples/impact-brief/script.performed.json",
        ):
            ep = load_episode(ROOT / rel)
            result = validate_episode(ep, preset_id="general")
            self.assertTrue(result.ok, [f"{i.path}: {i.message}" for i in result.issues])

    def test_performed_ok_on_roberto(self) -> None:
        ep = load_episode(ROOT / "examples/impact-brief/script.performed.json")
        result = validate_episode(ep, preset_id="roberto-agent")
        self.assertTrue(result.ok, [f"{i.path}: {i.message}" for i in result.issues])

    def test_dramatic_ok_general_fails_roberto(self) -> None:
        ep = load_episode(ROOT / "examples/genre-snippets/dramatic.performed.json")
        g = validate_episode(ep, preset_id="general")
        self.assertTrue(g.ok, [f"{i.path}: {i.message}" for i in g.issues])
        r = validate_episode(ep, preset_id="roberto-agent")
        self.assertFalse(r.ok)
        blob = " ".join(i.message for i in r.issues)
        self.assertIn("cry", blob)

    def test_musical_ok_general_fails_roberto(self) -> None:
        ep = load_episode(ROOT / "examples/genre-snippets/musical.performed.json")
        g = validate_episode(ep, preset_id="general")
        self.assertTrue(g.ok, [f"{i.path}: {i.message}" for i in g.issues])
        r = validate_episode(ep, preset_id="roberto-agent")
        self.assertFalse(r.ok)

    def test_roberto_sfx_cap(self) -> None:
        ep = load_episode(ROOT / "examples/impact-brief/script.performed.json")
        ep = json.loads(json.dumps(ep))
        ep["sfx_plan"].extend(
            [
                {"id": "w1", "kind": "section-whoosh"},
                {"id": "o1", "kind": "outro"},
            ]
        )
        r = validate_episode(ep, preset_id="roberto-agent")
        self.assertFalse(r.ok)


class ThresholdTests(unittest.TestCase):
    def test_overacted_reject(self) -> None:
        answers = {"answers": {"delivery_path": {"choice": "overacted_reject"}}}
        gate = apply_thresholds(answers, {"ship_noul_min": 0.8})
        self.assertIn("rewrite_overacted", gate["actions"])
        self.assertFalse(gate["ship"])

    def test_unearned_cry(self) -> None:
        answers = {
            "answers": {
                "delivery_path": {"choice": "somber_cry"},
                "somber_path_ok": {"noul": 0.1},
                "credibility_holds": {"noul": 0.9},
                "one_idea_clarity": {"score": 3.0},
                "flat_vs_overacted": {"score": 2.2},
            }
        }
        gate = apply_thresholds(answers, load_preset("general")["jev_thresholds"])
        self.assertIn("strip_somber_tags", gate["actions"])


class CliDryRunTests(unittest.TestCase):
    def _run(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "pipeline" / "render_episode.py"), *argv],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validate_and_render_dry_run(self) -> None:
        ep = "examples/impact-brief/script.performed.json"
        v = self._run("validate", ep)
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
        r = self._run("render", ep, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("dry-run", r.stdout)
        s = self._run("score", ep, "--dry-run")
        self.assertEqual(s.returncode, 0, s.stdout + s.stderr)
        self.assertIn("delivery_path", s.stdout)


if __name__ == "__main__":
    unittest.main()
