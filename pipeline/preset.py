"""Load and merge studio presets. Default is general (full tag set)."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from pipeline.paths import PRESETS_DIR


def preset_path(preset_id: str) -> Path:
    stem = preset_id.strip().replace(" ", "-")
    path = PRESETS_DIR / f"{stem}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Unknown preset '{preset_id}'. Add {path.name} under presets/ "
            f"(copy general.json). See presets/README.md."
        )
    return path


def load_preset(preset_id: str | None = None) -> dict[str, Any]:
    pid = preset_id or os.environ.get("PODCAST_PRESET") or "general"
    data = json.loads(preset_path(pid).read_text(encoding="utf-8"))
    return deepcopy(data)


def resolve_preset_id(cli_preset: str | None, episode: dict[str, Any] | None) -> str:
    if cli_preset:
        return cli_preset
    if episode and episode.get("preset"):
        return str(episode["preset"])
    return os.environ.get("PODCAST_PRESET") or "general"


def list_presets() -> list[str]:
    return sorted(p.stem for p in PRESETS_DIR.glob("*.json") if p.name != "preset.schema.json")
