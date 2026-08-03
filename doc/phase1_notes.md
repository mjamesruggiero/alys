# Phase 1 — Ingest & Clean: decisions & findings

## Pipeline shape (`src/alys/ingest.py`)

`build()` runs a chain of mostly-pure functions:

1. `load_raw` — concat every `Streaming_History_Audio_*.json`. *(side-effecting: reads disk)*
2. `strip_pii` — drop `ip_addr` immediately, before anything else touches the frame. *(pure)*
3. `filter_music` — keep rows with a non-null `spotify_track_uri`, dropping
   podcast/video/udiobook events. *(pure)*
4. `clean` — rename verbose Spotify fields, parse `ts` → tz-aware UTC, dedup on
   `(ts, track_uri)`, add `meaningful_listen` flag, select useful columns. *(pure)*

Keeping transforms pure (input frame → output frame) makes functions unit-testable. 
Only `load_raw` and the Parquet write are side-effecting, sitting the edges.
(cf. [Bernhardt, Functional Core, Imperative Shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell).)

## Plays overview

Observed on the real export (247,691 music plays after cleaning):

| Year | Plays |
|------|-------|
| 2013 | 32 |
| 2014 | 25 |
| 2015 | 1,463 |
| 2016 | 647 |
| 2017 | 22,970 |
| 2018 | 31,252 |
| 2019 | 30,801 |
| 2020 | 28,409 |
| 2021 | 33,916 |
| 2022 | 9,480 |
| 2023 | 28,067 |
| 2024 | 28,805 |
| 2025 | 20,541 |
| 2026 | 11,283 |

## "Meaningful listen" threshold

`config.yaml → ingest.min_listen_ms = 30000` (30 s). Currently 75.2% of plays
clear this bar. The 30 s value is a starting default borrowed from the industry
"counts as a stream" convention; it will be **justified empirically with a
histogram** of `ms_played` in the Phase 2 notebook (and revisited if distribution suggests a better cut).

## Reproducibility sample

`scripts/make_sample.py` writes a small, seeded slice to
`data/sample/plays_sample.parquet` (committed). The full interim table stays
gitignored because it derives from a private export. The sample is PII-free by
construction — it's drawn *after* `strip_pii`.
