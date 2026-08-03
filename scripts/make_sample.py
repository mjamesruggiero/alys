#!/usr/bin/env python
"""Create a small, committable sample of the cleaned plays dataset.

The full ``data/interim/plays.parquet`` is gitignored (it's derived from a
private export). For reproducibility we commit a tiny slice under
``data/sample/`` so anyone cloning the repo can run the notebooks and tests
against *some* real-shaped data.

Privacy: the sample is drawn from the already-cleaned table, which has had
``ip_addr`` and all other PII stripped in ``ingest.py``. Track/artist/album
names are not sensitive, so they are kept as-is to make the sample useful.
"""

import argparse
import logging

import pandas as pd

from alys import config

logger = logging.getLogger(__name__)


def make_sample(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Return a deterministic n-row sample, sorted by time (pure function)."""
    n = min(n, len(df))
    return df.sample(n=n, random_state=seed).sort_values("ts").reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in",
        dest="in_path",
        default=str(config.INTERIM_DIR / "plays.parquet"),
        help="Cleaned plays parquet to sample from (default: data/interim/plays.parquet).",
    )
    parser.add_argument(
        "--out",
        default=str(config.SAMPLE_DIR / "plays_sample.parquet"),
        help="Where to write the sample (default: data/sample/plays_sample.parquet).",
    )
    parser.add_argument(
        "-n",
        "--rows",
        type=int,
        default=500,
        help="Number of rows to sample (default: 500).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for a reproducible sample (default: 42).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    df = pd.read_parquet(args.in_path)
    sample = make_sample(df, n=args.rows, seed=args.seed)

    config.SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    sample.to_parquet(args.out, index=False)
    logger.info("Wrote %s-row sample to %s", f"{len(sample):,}", args.out)


if __name__ == "__main__":
    main()
