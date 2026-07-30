"""Project paths and tunable constants."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = Path(os.path.expanduser(os.getenv("SPOTIFY_RAW_DIR", DATA_DIR / "raw")))
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"

# --- Modeling constants (justify empirically in the notebooks) ---
# A play counts as a "meaningful listen" at/above this many ms.
MIN_LISTEN_MS = 30_000
# Gap (seconds) above which a new listening session begins.
SESSION_GAP_SECONDS = 30 * 60

# --- API keys (loaded from .env) ---
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET", "")
