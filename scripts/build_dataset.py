#!/usr/bin/env python
"""Build the cleaned plays dataset from the raw Spotify export."""

import argparse
import logging

from alys import config, ingest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest raw Spotify streaming history into a clean plays.parquet."
    )
    parser.add_argument(
        "--raw-dir",
        default=str(config.RAW_DIR),
        help="Directory of Streaming_History_Audio_*.json files "
        "(default: SPOTIFY_RAW_DIR env var, else data/raw).",
    )
    parser.add_argument(
        "--out",
        default=str(config.INTERIM_DIR / "plays.parquet"),
        help="Output Parquet path (default: data/interim/plays.parquet).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    df = ingest.build(raw_dir=args.raw_dir, out_path=args.out)
    ingest.log_summary(df, args.out)


if __name__ == "__main__":
    main()
