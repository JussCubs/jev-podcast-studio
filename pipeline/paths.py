from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRESETS_DIR = REPO_ROOT / "presets"
RUBRICS_DIR = REPO_ROOT / "rubrics"
SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"
TAGS_PATH = Path(__file__).resolve().parent / "speech_tags.json"
EPISODE_SCHEMA_PATH = SCHEMAS_DIR / "episode.schema.json"
