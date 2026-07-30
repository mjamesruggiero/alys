# Spotify Taste Profile — Project Plan

A public, portfolio-quality ML project built on my own Spotify extended streaming
history. The goal: learn statistics and ML fundamentals, build something genuinely
fun, and produce an artifact that demonstrates real skills (EDA, feature
engineering, and a working recommender) to prospective employers.

---

## 1. The Big Idea

Combine three pillars into one coherent story:

1. **Session detection** — reconstruct listening "sessions" from raw play events
   using inter-play time gaps (an unsupervised, statistics-flavored problem).
2. **Audio / content features** — attach descriptive features to tracks (genre,
   audio characteristics, or embeddings) so tracks live in a feature space.
3. **A recommender** — build a personal "taste profile" and generate
   recommendations two ways:
   - **Content-based**: cosine similarity in the track feature space.
   - **Collaborative / latent**: matrix factorization over a listener×track (or
     session×track) implicit-feedback matrix.

The narrative payoff: **compare my model's recommendations against what Spotify
actually served me** (e.g., tracks that arrived via `reason_start = "trackdone"`
in an autoplay/radio context, or shuffle behavior), and measure agreement. This
touches EDA, feature engineering, unsupervised learning, and a real model — end
to end.

---

## 2. What the Data Actually Looks Like

*(Verified by inspecting `~/Desktop/debris/spotify_data`.)*

- **~252,000 audio play events**, **~75,800 unique tracks**, **~16,800 unique
  artists**, spanning **2013 → 2026** (the 2026 timestamps are almost certainly
  export/timezone artifacts — clean/inspect these).
- Files: `Streaming_History_Audio_YYYY[_N].json` (music) and
  `Streaming_History_Video_YYYY.json` (podcasts/video — filter these out for the
  core music model, or keep as a separate side analysis).
- The `_1` / `_2` suffixed files are **separate chunks, not duplicates** (verified
  zero timestamp overlap), but still run a dedup safety check on `ts` +
  `spotify_track_uri`.

**Per-play fields available (the good stuff):**

| Field | Use |
|---|---|
| `ts` | Event timestamp (UTC) → time features, session gaps |
| `ms_played` | Engagement signal; define a "real listen" threshold |
| `master_metadata_track_name` | Track identity |
| `master_metadata_album_artist_name` | Artist |
| `master_metadata_album_album_name` | Album |
| `spotify_track_uri` | Stable track key (join key for features) |
| `reason_start` / `reason_end` | `clickrow`, `trackdone`, `fwdbtn`, `appload`… → intent & autoplay detection |
| `shuffle` | Boolean |
| `skipped` | Boolean (great implicit negative signal) |
| `platform` | Device/context |
| `conn_country`, `offline`, `incognito_mode` | Context / filtering |
| `episode_name`, `audiobook_*` | Non-music rows to filter out |

**Privacy note:** the raw JSON contains `ip_addr`. **Never commit raw data.** Strip
`ip_addr` and other PII in the very first ingest step, and `.gitignore` the raw
data directory. Ship only a small, anonymized sample for reproducibility.

---

## 3. ⚠️ Critical Constraint: The Audio Features API Is Deprecated

As of **November 2024**, Spotify **deprecated the `/audio-features` endpoint**
(danceability, energy, valence, tempo, etc.) and the related recommendations
endpoint for new/unprivileged apps. Do **not** design the project assuming you can
pull those features. Plan for one of these fallbacks (in rough order of
recommendation):

- **Option A — MusicBrainz + AcousticBrainz / ListenBrainz** (open, free): map
  tracks via ISRC/artist+title and pull genre tags and (where available) acoustic
  features. Fully open-data friendly; great for a public repo.
- **Option B — Last.fm API** (free key): pull artist/track **genre tags** and
  similarity. Excellent for a content-based model even without raw audio DSP.
- **Option C — Compute your own audio features** with `librosa` on 30-second
  preview clips (if you can source previews). Most "ML from scratch" credibility,
  but the most work and the flakiest sourcing.
- **Option D — Behavioral / metadata-only features**: skip audio DSP entirely and
  build features purely from listening behavior + artist/genre metadata. The
  matrix-factorization model needs **no** audio features at all — it learns latent
  taste vectors directly from play counts.

**Recommended path:** start with **Option D** (behavioral MF works immediately on
data you already have), then layer in **Option B (Last.fm genre tags)** for the
content-based model and the "audio features" learning goal. Treat Options A/C as
stretch goals.

---

## 4. Repository Structure

```
spotify-taste-profile/
├── README.md                     # Story-driven: problem, findings, visuals, how-to-run
├── LICENSE                       # MIT
├── pyproject.toml                # Deps + tooling (or requirements.txt to start)
├── .gitignore                    # Ignore data/raw/, .env, caches, checkpoints
├── .env.example                  # Template for API keys (Last.fm etc.)
├── Makefile                      # `make data`, `make features`, `make train`, `make report`
│
├── data/
│   ├── raw/                      # .gitignored — the untouched Spotify export
│   ├── interim/                  # Cleaned/deduped parquet
│   ├── processed/                # Model-ready tables (sessions, features, matrices)
│   └── sample/                   # SMALL anonymized sample committed for reproducibility
│
├── notebooks/                    # Numbered, narrative EDA & experiments
│   ├── 01_data_overview.ipynb
│   ├── 02_eda_listening_patterns.ipynb
│   ├── 03_session_detection.ipynb
│   ├── 04_feature_engineering.ipynb
│   ├── 05_content_based_recommender.ipynb
│   ├── 06_matrix_factorization.ipynb
│   └── 07_model_vs_spotify.ipynb
│
├── src/spotify_taste/            # Importable, tested package (the "engineer" signal)
│   ├── __init__.py
│   ├── config.py                 # Paths, thresholds, constants
│   ├── ingest.py                 # Load JSON, strip PII, filter music, dedup
│   ├── sessions.py               # Sessionization from time gaps
│   ├── features.py               # Track/behavioral/genre feature builders
│   ├── enrich.py                 # External API clients (Last.fm / MusicBrainz), cached
│   ├── recommenders/
│   │   ├── content_based.py      # Cosine-similarity model
│   │   └── matrix_factorization.py  # Implicit-feedback MF (ALS)
│   ├── evaluation.py             # Metrics + Spotify-comparison logic
│   └── viz.py                    # Reusable plotting helpers
│
├── scripts/                      # Thin CLI entry points calling src/
│   ├── build_dataset.py
│   ├── train_models.py
│   └── evaluate.py
│
├── tests/                        # pytest — even a few tests stand out in ML repos
│   ├── test_ingest.py
│   ├── test_sessions.py
│   └── test_recommenders.py
│
├── reports/
│   └── figures/                  # Exported charts used in README
│
└── .github/workflows/ci.yml      # Lint + tests on push (shows engineering rigor)
```

Rationale: this borrows from the **Cookiecutter Data Science** layout. The
`src/` package + `tests/` + CI is what separates a "notebook dump" from something
that reads as professional engineering.

---

## 5. Libraries

**Core**
- `python` 3.11+
- `pandas`, `numpy` — wrangling
- `pyarrow` — fast Parquet I/O
- `scipy` — sparse matrices, stats
- `scikit-learn` — cosine similarity, `TruncatedSVD`, metrics, preprocessing

**Recommender**
- `implicit` — battle-tested ALS matrix factorization for implicit feedback
  (the right tool for play-count data), or hand-roll SVD/ALS as a learning
  exercise and compare.

**Visualization**
- `matplotlib` + `seaborn` (core)
- `plotly` (optional, for interactive listening-timeline visuals in README)

**Enrichment (pick per Section 3)**
- `requests` + `requests-cache` (or `tenacity` for retries) — polite, cached API calls
- `musicbrainzngs` — if using MusicBrainz
- `pylast` — if using Last.fm
- `librosa` — only if computing your own audio features (Option C)

**Tooling / quality**
- `jupyter` / `jupyterlab`
- `ruff` (lint + format — fast, one tool), `mypy` (optional typing)
- `pytest`
- `python-dotenv` — API keys from `.env`
- `pre-commit` — auto-run ruff/tests before commits
- Environment: `uv` (fast) or `conda`/`venv` — your choice; pin versions.

Keep the initial install lean; add enrichment/`librosa` only when you reach that phase.

---

## 6. Step-by-Step Roadmap (Phased)

Each phase is a shippable milestone with its own PR/commit and README update.
Ship early, ship ugly, iterate — a green repo with commits over time tells a story.

### Phase 0 — Repo bootstrap (½ day)
- [ ] `git init`, create repo scaffold above, add MIT `LICENSE`, `.gitignore`.
- [ ] Set up environment + `pyproject.toml`, install core libs.
- [ ] Add `ruff` + `pytest` + a trivial CI workflow so it's green from day one.
- [ ] Write a skeleton README stating the goal (fill in results as you go).

### Phase 1 — Ingest & clean (1–2 days)
- [ ] `ingest.py`: load all `Streaming_History_Audio_*.json`, concat.
- [ ] **Strip `ip_addr` and PII immediately.** Filter out video/podcast/audiobook
      rows (keep rows with a non-null `spotify_track_uri`).
- [ ] Dedup on (`ts`, `spotify_track_uri`). Parse `ts` → tz-aware datetime.
- [ ] Investigate the 2013 and 2026 boundary timestamps; document decisions.
- [ ] Define a **"meaningful listen"** (e.g., `ms_played >= 30_000` or
      `>= 50%` of track length if you can get durations). Justify the threshold
      with a histogram — this is your first bit of applied statistics.
- [ ] Write cleaned data to `data/interim/plays.parquet`. Commit a small
      anonymized `data/sample/`.
- [ ] Tests: row counts, no PII columns, no non-music rows leak through.

### Phase 2 — EDA (2–3 days) — *the statistics playground*
- [ ] Listening over time: plays/day, by hour-of-day, day-of-week, seasonality.
- [ ] Top artists/tracks/albums; long-tail (Zipf/power-law) analysis of play counts.
- [ ] Engagement: `ms_played` distribution, `skipped` rate by context/artist.
- [ ] Behavior: `shuffle` usage over time, `reason_start`/`reason_end` breakdown
      (this is where you *find* Spotify's autoplay/radio in the data).
- [ ] Taste drift: how top genres/artists shift year over year.
- [ ] Stats touchpoints: distributions & summary stats, correlation, a hypothesis
      test or two (e.g., is skip rate higher on shuffle? χ²/proportion test),
      confidence intervals. Keep it honest and well-annotated.
- [ ] Export the best figures to `reports/figures/` for the README.

### Phase 3 — Session detection (1–2 days)
- [ ] `sessions.py`: sort by time, compute inter-play gaps, split into sessions
      when gap > threshold (e.g., 30 min). Justify the threshold empirically by
      plotting the gap distribution and looking for the natural elbow.
- [ ] Per-session features: length, duration, distinct artists, skip rate,
      shuffle share, time-of-day, "discovery vs. comfort" ratio.
- [ ] EDA on sessions: typical session shape, weekday vs. weekend, etc.
- [ ] Tests: sessionization edge cases (single play, exact-threshold gaps).

### Phase 4 — Feature engineering (2–4 days)
- [ ] Behavioral track features (no external API needed): total plays, unique
      days, completion rate, skip rate, recency, first/last seen.
- [ ] `enrich.py`: fetch genre tags (Last.fm) and/or MusicBrainz metadata for the
      **top-N tracks/artists** (don't hammer APIs for all 75k tracks — start with
      the head of the distribution). **Cache aggressively** to disk.
- [ ] Build a track feature matrix (behavioral + one-hot/embedded genres).
      Standardize/scale as appropriate.
- [ ] Tests: feature matrix has no leakage from the target, no NaNs where illegal.

### Phase 5 — Content-based recommender (2 days)
- [ ] `content_based.py`: represent each track as a feature vector; build a
      **taste profile** as the (engagement-weighted) centroid of tracks I love.
- [ ] Recommend via cosine similarity between the profile (or a seed track) and
      the catalog; exclude already-heard tracks.
- [ ] Sanity-check: do recommendations "make sense"? Show qualitative examples.

### Phase 6 — Matrix factorization (3–4 days) — *the real model*
- [ ] Build an implicit-feedback matrix. Since it's single-user, use
      **session × track** (or **week × track**) as the "user" axis so MF has
      structure to learn from. Weight by play count / engagement.
- [ ] Train ALS with `implicit` (and optionally a from-scratch SVD baseline).
- [ ] Inspect latent factors: cluster tracks in latent space, name the clusters
      ("late-night electronic," "gym hip-hop") — a compelling README visual.
- [ ] Proper evaluation: temporal train/test split (train on past, test on
      future), report **Precision@k, Recall@k, MAP, NDCG**. Compare against a
      popularity baseline and the content-based model.

### Phase 7 — Model vs. Spotify (2–3 days) — *the payoff*
- [ ] Identify tracks Spotify "served" me (autoplay/radio/recommended contexts via
      `reason_start`, non-`clickrow` starts, shuffle-introduced tracks).
- [ ] Ask: would my model have recommended those? Compute overlap / rank
      agreement between my recommendations and Spotify's served tracks.
- [ ] Discuss honestly: where do we agree, where diverge, and *why* (filter
      bubble, exploration vs. exploitation, cold-start). This reflective analysis
      is what makes the project memorable.

### Phase 8 — Polish & publish (2 days)
- [ ] README as a **narrative**: hook → questions → method → visuals → findings →
      limitations → how to reproduce. Lead with your best figure.
- [ ] Clean notebooks (run top-to-bottom, clear noisy output).
- [ ] Ensure CI is green, tests pass, `ruff` clean.
- [ ] Optional: a short blog post / write-up linked from the README.
- [ ] Add topics/tags on GitHub; pin the repo on your profile.

---

## 7. What This Demonstrates to Employers

- **EDA & storytelling:** turning raw JSON into insight with clear visuals.
- **Statistics:** distributions, hypothesis testing, threshold justification,
  power-law/long-tail reasoning.
- **Feature engineering:** behavioral + external-data enrichment with caching.
- **ML modeling:** two recommender paradigms, proper temporal evaluation, and
  baselines (not just "I trained a model").
- **Software engineering:** packaged `src/`, tests, CI, reproducibility, clean git
  history — the things that separate hobby notebooks from hireable work.
- **Judgment:** handling a real deprecated-API constraint, protecting PII, and
  writing an honest limitations section.

---

## 8. Scope Guardrails (so it actually ships)

- **MVP first:** Phases 0–2 alone (ingest + EDA) are already a respectable public
  repo. Ship that, then keep building in public.
- The single-user setting makes classic collaborative filtering unusual — lean
  into it as a **feature** ("a recommender for an audience of one") and use the
  session×track trick.
- Don't try to enrich all 75k tracks. Head of the distribution covers most plays.
- Timebox enrichment/API work; it's the most likely rabbit hole.

---

## 9. Immediate Next Actions

1. Confirm the enrichment path (recommend: **behavioral MF + Last.fm tags**).
2. Pick tooling (`uv` vs. `venv`/`conda`) and Python version.
3. Approve the repo name (`spotify-taste-profile`?) and scaffold Phase 0.
4. Then start Phase 1 ingest against the real files in `~/Desktop/debris/spotify_data`.
