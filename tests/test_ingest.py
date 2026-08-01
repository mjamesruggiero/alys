"""Tests for the Phase 1 ingest pipeline."""

import json

import pandas as pd
import pytest

from alys import ingest

# A minimal raw record with all the fields the pipeline touches.
BASE = {
    "ts": "2020-01-01T12:00:00Z",
    "ip_addr": "50.1.107.42",
    "ms_played": 200_000,
    "conn_country": "US",
    "master_metadata_track_name": "Song A",
    "master_metadata_album_artist_name": "Artist A",
    "master_metadata_album_album_name": "Album A",
    "spotify_track_uri": "spotify:track:aaa",
    "spotify_episode_uri": None,
    "reason_start": "clickrow",
    "reason_end": "trackdone",
    "shuffle": False,
    "skipped": False,
    "offline": False,
    "incognito_mode": False,
    "platform": "osx",
}


def _rec(**overrides):
    return {**BASE, **overrides}


@pytest.fixture
def raw_dir(tmp_path):
    """Write a couple of raw audio JSON files, plus a non-music row."""
    records = [
        _rec(),  # music
        _rec(ts="2020-01-01T12:10:00Z", spotify_track_uri="spotify:track:bbb", ms_played=5_000),
        # podcast/video row: no track uri -> must be filtered out
        _rec(
            spotify_track_uri=None,
            master_metadata_track_name=None,
            spotify_episode_uri="spotify:episode:xyz",
        ),
    ]
    (tmp_path / "Streaming_History_Audio_2020.json").write_text(json.dumps(records))
    # duplicate of the first record in a second file -> must be deduped
    (tmp_path / "Streaming_History_Audio_2020_1.json").write_text(json.dumps([_rec()]))
    return tmp_path


def test_strip_pii_removes_ip():
    df = pd.DataFrame([_rec()])
    out = ingest.strip_pii(df)
    assert "ip_addr" not in out.columns


def test_filter_music_drops_non_track_rows():
    df = pd.DataFrame([_rec(), _rec(spotify_track_uri=None)])
    out = ingest.filter_music(df)
    assert len(out) == 1


def test_build_end_to_end(raw_dir, tmp_path):
    out_path = tmp_path / "plays.parquet"
    df = ingest.build(raw_dir=raw_dir, out_path=out_path)

    # No PII survives.
    assert "ip_addr" not in df.columns
    # Non-music row filtered, duplicate removed -> 2 unique music plays.
    assert len(df) == 2
    # Friendly column names present.
    assert {"track_uri", "track_name", "artist_name"} <= set(df.columns)
    # tz-aware timestamps, sorted ascending.
    assert str(df["ts"].dt.tz) == "UTC"
    assert df["ts"].is_monotonic_increasing
    # Meaningful-listen flag: 200s yes, 5s no.
    assert df["meaningful_listen"].tolist() == [True, False]
    # Parquet was written and round-trips.
    assert out_path.exists()
    assert len(pd.read_parquet(out_path)) == 2
