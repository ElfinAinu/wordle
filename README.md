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
- `infographic-v4.html` — the shipped poster (static, self-contained)
- `poster.py` — regenerates the legacy `infographic.html` from results

## Core pipeline

| Script        | Produces                                       |
| ------------- | ---------------------------------------------- |
| `analyze.py`  | letter/slot frequencies → `results/analysis.*` |
| `coverage.py` | opener-pair scoring → `results/coverage.*`     |
| `pairs.py`    | best disjoint letter pairs → `results/pairs.*` |
| `hit_tree.py` | hit-count play tree → `results/hit_tree.*`     |

One-off explorations (also in `results/`): `exhaustive.py`, `heatmaps.py`,
`shapes.py`, `vowel_tree.py`, `after_gray.py`, `compare.py`.

## Run

Python 3.11+ with numpy + matplotlib. No package config, so:

```
uv run --with numpy --with matplotlib python <script>.py
```

(or any venv with the same deps) — from the repo root; scripts expect `data/`
and `results/` alongside.
