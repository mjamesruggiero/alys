"""Phase 1: ingest raw Spotify extended streaming history.

Responsibilities (in order):
    1. Load every ``Streaming_History_Audio_*.json`` file.
    2. Strip PII (``ip_addr``) immediately.
    3. Keep only music rows (drop podcast/video/audiobook events).
    4. Deduplicate on (ts, track_uri).
    5. Parse timestamps to tz-aware UTC and add a "meaningful listen" flag.
    6. Write a tidy Parquet table to ``data/interim/plays.parquet``.

Run via ``scripts/build_dataset.py`` or ``python -m alys.ingest``.
"""

from __future__ import annotations

import glob
import json
import logging
from pathlib import Path

import pandas as pd

from alys import config

logger = logging.getLogger(__name__)

# Columns that must never leave this module / hit disk in the clean data.
PII_COLUMNS = ["ip_addr"]

# Verbose Spotify field -> friendly name.
RENAME_MAP = {
    "master_metadata_track_name": "track_name",
    "master_metadata_album_artist_name": "artist_name",
    "master_metadata_album_album_name": "album_name",
    "spotify_track_uri": "track_uri",
}

AUDIO_GLOB = "Streaming_History_Audio_*.json"


def load_raw(raw_dir: Path | str = config.RAW_DIR) -> pd.DataFrame:
    """Load and concatenate all audio streaming-history JSON files."""
    raw_dir = Path(raw_dir).expanduser()
    files = sorted(glob.glob(str(raw_dir / AUDIO_GLOB)))
    if not files:
        raise FileNotFoundError(f"No files matching {AUDIO_GLOB!r} under {raw_dir}")

    frames = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            frames.append(pd.DataFrame(json.load(fh)))
    return pd.concat(frames, ignore_index=True)


def strip_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Drop any known PII columns. Safe if the columns are absent."""
    return df.drop(columns=[c for c in PII_COLUMNS if c in df.columns])


def filter_music(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only music plays (rows with a Spotify track URI).

    Drops podcasts, video (``spotify_episode_uri``), audiobook rows, which
    have a null ``spotify_track_uri``.
    """
    return df[df["spotify_track_uri"].notna()].copy()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Rename, parse timestamps, dedup, and add derived columns."""
    df = df.rename(columns=RENAME_MAP)

    # tz-aware UTC timestamps.
    df["ts"] = pd.to_datetime(df["ts"], utc=True)

    # Dedup on the natural key: same track played at the same instant.
    df = df.drop_duplicates(subset=["ts", "track_uri"]).sort_values("ts")

    # Engagement flag: was this a "meaningful listen"?
    df["meaningful_listen"] = df["ms_played"] >= config.MIN_LISTEN_MS

    # Keep only the columns useful downstream, dropping podcast/audiobook cruft.
    keep = [
        "ts",
        "track_uri",
        "track_name",
        "artist_name",
        "album_name",
        "ms_played",
        "meaningful_listen",
        "reason_start",
        "reason_end",
        "shuffle",
        "skipped",
        "offline",
        "incognito_mode",
        "conn_country",
        "platform",
    ]
    keep = [c for c in keep if c in df.columns]
    return df[keep].reset_index(drop=True)


def build(
    raw_dir: Path | str = config.RAW_DIR,
    out_path: Path | str | None = None,
) -> pd.DataFrame:
    """Full pipeline: load -> strip PII -> filter -> clean -> write Parquet."""
    df = load_raw(raw_dir)
    df = strip_pii(df)
    df = filter_music(df)
    df = clean(df)

    if out_path is None:
        out_path = config.INTERIM_DIR / "plays.parquet"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)

    return df


def log_summary(df: pd.DataFrame, out_path: Path | str) -> None:
    """Log a human-readable summary of the built dataset."""
    logger.info("Wrote %s plays to %s", f"{len(df):,}", out_path)
    logger.info("  unique tracks : %s", f"{df['track_uri'].nunique():,}")
    logger.info("  unique artists: %s", f"{df['artist_name'].nunique():,}")
    logger.info("  date range    : %s -> %s", df["ts"].min(), df["ts"].max())
    logger.info("  meaningful    : %.1f%% of plays", df["meaningful_listen"].mean() * 100)
