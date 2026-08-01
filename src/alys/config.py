"""Project configuration.

Structural paths and API keys live here (they're part of the code's shape).
Tunable modeling constants are loaded from ``config.yaml`` at the project root
so they can be edited without touching code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = Path(os.path.expanduser(os.getenv("SPOTIFY_RAW_DIR", str(DATA_DIR / "raw"))))
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"

CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(path: Path | str = CONFIG_PATH) -> dict[str, Any]:
    """Load the YAML config of tunable constants."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


_cfg = load_config()

# --- Tunable modeling constants (from config.yaml) ---
MIN_LISTEN_MS: int = _cfg["ingest"]["min_listen_ms"]
SESSION_GAP_SECONDS: int = _cfg["sessions"]["session_gap_seconds"]

# --- API keys (loaded from .env) ---
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET", "")
