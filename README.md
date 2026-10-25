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
- `.scratch/*/checks/` — per-ticket acceptance checks that re-derive the
  poster's figures from committed inputs
- `tests/` — regression checks for shared analysis code (see Test)

## Publish

`publish_poster.py` copies `infographic-v4.html` from the default branch
(`main`) onto `index.html` on the served branch (`gh-pages`) and removes the
duplicate poster there. It runs the guards and refuses to write if a retracted
claim survives, a hit-count band names a guess word, or the served copy does
not match the source afterwards. It is idempotent and never pushes.

The band guard reads sections I and II only. Those are the band-level panels:
each row is a hit count whose Strategy cell must state a mix, so a guess word
there is a bug. Sections III and IV name the recommended word per pattern,
which is the point of the row, so they are not guarded as bands; the
acceptance check covers a word leaking into a section III or IV heading.

```
python3 publish_poster.py            # run the guards, then publish
python3 publish_poster.py --check    # run the guards only
```

## Test

`tests/test_pattern_codes.py` is the regression check for the one shared
Wordle feedback function (`analyze.pattern_codes`). It compares the shared
function against an independent pure-Python reference over every answer and a
set of guesses that repeat a letter, and pins the previous implementation's
known mismatch counts.

```
uv run --with numpy python tests/test_pattern_codes.py
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
`shapes.py`, `duplicates.py`, `repeat_shapes.py`, `vowel_tree.py`,
`full_coverage.py`, `after_gray.py`, `compare.py`.

## Run

Python 3.11+ with numpy + matplotlib. No package config, so:

```
uv run --with numpy --with matplotlib python <script>.py
```

(or any venv with the same deps) — from the repo root; scripts expect `data/`
and `results/` alongside.
