# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Exhaustive disjoint-pair check over a chosen candidate universe.

Universe "answers": candidates = past answers (NYT's published pool).
Universe "all": candidates = past answers + every valid guess
(BUMPY-proof: assumes the server may promote any guessable word).
Guesses always come from the full guessable pool in both universes.

Ranks fixed disjoint pairs by expected remaining candidates after two
guesses. Usage: uv run exhaustive.py [answers|all]
"""

import json
import sys

import numpy as np

from analyze import (
    ALLOWED_PATH,
    ANSWERS_PATH,
    RESULTS_DIR,
    encode,
    letter_counts,
    load_words,
    pattern_codes,
    rank_openers,
)
from coverage import letter_masks

FIRST_POOL = 300
BASELINE = ("soare", "clint")
PATTERN_SPACE = 3**5
COMBINED_SPACE = PATTERN_SPACE * PATTERN_SPACE


def score_combined(combined: np.ndarray, total: int) -> tuple[float, float]:
    counts = np.bincount(combined, minlength=COMBINED_SPACE)
    nonzero = counts[counts > 0].astype(np.float64)
    remaining = float((nonzero**2).sum() / total)
    solved = 100 * float((nonzero == 1).sum()) / total
    return remaining, solved


def main() -> None:
    universe = sys.argv[1] if len(sys.argv) > 1 else "all"
    answers = load_words(ANSWERS_PATH)
    guess_pool = sorted(set(answers) | set(load_words(ALLOWED_PATH)))
    universe_words = answers if universe == "answers" else guess_pool

    universe_codes = encode(universe_words)
    universe_counts = letter_counts(universe_codes)
    universe_masks = letter_masks(universe_words)
    distinct_counts = universe_masks.sum(axis=1)
    total = len(universe_words)
    letter_spot_weights = (
        universe_masks.astype(np.float64) / distinct_counts[:, None]
    ).sum(axis=0)

    guess_masks = letter_masks(guess_pool) if universe == "answers" else universe_masks
    guess_index = {word: i for i, word in enumerate(guess_pool)}

    print(f"universe: {universe} ({total} candidates); precomputing patterns...")
    pattern_of = {
        word: pattern_codes(encode([word])[0], universe_codes, universe_counts)
        for word in guess_pool
    }

    first_words = [
        row["word"]
        for row in rank_openers(guess_pool, universe_words, FIRST_POOL)["top"]
    ]

    scored = []
    seen = set()
    for first in first_words:
        first_mask = guess_masks[guess_index[first]]
        first_patterns = pattern_of[first]
        for second_index, second in enumerate(guess_pool):
            if (guess_masks[second_index] & first_mask).any():
                continue
            pair_key = tuple(sorted((first, second)))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            combined = first_patterns * PATTERN_SPACE + pattern_of[second]
            remaining, solved = score_combined(combined, total)
            pair_mask = first_mask | guess_masks[second_index]
            spot = float(letter_spot_weights[pair_mask].sum() / total)
            scored.append(
                {
                    "first": pair_key[0],
                    "second": pair_key[1],
                    "expected_remaining": round(remaining, 3),
                    "solved_on_two_pct": round(solved, 2),
                    "spot_rate_pct": round(100 * spot, 1),
                }
            )

    scored.sort(key=lambda row: (row["expected_remaining"], -row["solved_on_two_pct"]))
    baseline_key = tuple(sorted(BASELINE))
    baseline = next(
        row for row in scored if (row["first"], row["second"]) == baseline_key
    )
    beaters = [
        row
        for row in scored
        if row["expected_remaining"] < baseline["expected_remaining"]
    ]

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / f"exhaustive_{universe}.json").write_text(
        json.dumps({"universe": universe, "pairs": scored[:50]}, indent=2)
    )
    candidate_desc = (
        "past answers only"
        if universe == "answers"
        else "past answers + every valid guess"
    )
    lines = [
        f"# Exhaustive disjoint-pair check, universe={universe} ({len(scored)} pairs)",
        "",
        f"Candidates: {total} ({candidate_desc}).",
        "",
        f"Baseline {BASELINE[0].upper()}+{BASELINE[1].upper()}: remaining {baseline['expected_remaining']}, "
        f"solved-on-2 {baseline['solved_on_two_pct']}%, spot {baseline['spot_rate_pct']}%.",
        f"Pairs beating baseline: **{len(beaters)}**.",
        "",
        "| # | Pair | Remaining | Solved2% | Spot% |",
        "|---|---|---|---|---|",
    ]
    for rank, row in enumerate(scored[:20], start=1):
        lines.append(
            f"| {rank} | {row['first'].upper()} + {row['second'].upper()} "
            f"| {row['expected_remaining']} | {row['solved_on_two_pct']} | {row['spot_rate_pct']} |"
        )
    (RESULTS_DIR / f"exhaustive_{universe}.md").write_text("\n".join(lines) + "\n")

    print(f"scored {len(scored)} pairs; {len(beaters)} beat baseline")
    print(f"baseline {BASELINE[0].upper()}+{BASELINE[1].upper()}: {baseline}")
    for row in scored[:10]:
        print(
            f"  {row['first'].upper():6} + {row['second'].upper():6} "
            f"remaining {row['expected_remaining']:7.2f} solved2 {row['solved_on_two_pct']:5.1f}% "
            f"spot {row['spot_rate_pct']}%"
        )


if __name__ == "__main__":
    main()
