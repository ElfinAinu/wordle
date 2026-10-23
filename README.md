# Wordle Strategy Analysis

**Live poster →
[elfinainu.github.io/wordle](https://elfinainu.github.io/wordle/)**

Analysis scripts and data behind the Wordle fixed-opening poster. The poster is
the write-up; this repo just produces it.

## Layout

- `data/` — raw inputs: `answers.txt` (2,309 answers), `allowed.txt` (12,546
  guesses)
- `*.py` — one analysis question per script
- `results/` — generated outputs (`*.md` + `*.json`)
- `infographic-v4.html` — the shipped poster (static, self-contained); this is the only poster
- `publish_poster.py` — the guarded one-step deploy to the served branch (see Publish)
- `.scratch/poster-fixes/checks/` — per-ticket acceptance checks that
  re-derive the poster's figures from committed inputs

## Publish

`publish_poster.py` copies `infographic-v4.html` from the default branch
(`main`) onto `index.html` on the served branch (`gh-pages`) and removes the
duplicate poster there. It runs the guards and refuses to write if a retracted
claim survives, a hit-count band names a guess word, or the served copy does
not match the source afterwards. It is idempotent and never pushes.

```
python3 publish_poster.py            # run the guards, then publish
python3 publish_poster.py --check    # run the guards only
```

## Core pipeline

| Script        | Produces                                       |
| ------------- | ---------------------------------------------- |
| `analyze.py`  | letter/slot frequencies → `results/analysis.*` |
| `coverage.py` | opener-pair scoring → `results/coverage.*`     |
| `pairs.py`    | best disjoint letter pairs → `results/pairs.*` |
| `hit_tree.py` | hit-count play tree → `results/hit_tree.*`     |
| `simulate_method.py` | taught fixed-opening simulation → `results/simulate_method.*` |

One-off explorations (also in `results/`): `exhaustive.py`, `heatmaps.py`,
`shapes.py`, `duplicates.py`, `vowel_tree.py`, `after_gray.py`, `compare.py`.

## Run

Python 3.11+ with numpy + matplotlib. No package config, so:

```
uv run --with numpy --with matplotlib python <script>.py
```

(or any venv with the same deps) — from the repo root; scripts expect `data/`
and `results/` alongside.
