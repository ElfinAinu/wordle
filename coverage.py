# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Rank disjoint opener pairs: guess 1 + guess 2 share no letters.

Two fixed guesses test 10 distinct letters, so guesses 1-2 purely spot
which letters are in the answer. Metrics per pair:
- expected remaining candidates after both feedbacks (information)
- spot rate: mean share of each answer's distinct letters tested
"""

import json

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

FIRST_GUESS_POOL = 150
PATTERN_SPACE = 3**5
TOP_PAIRS = 25


def letter_masks(words: list[str]) -> np.ndarray:
    masks = np.zeros((len(words), 26), dtype=bool)
    for index, word in enumerate(words):
        for ch in set(word):
            masks[index, ord(ch) - 97] = True
    return masks


def word_mask(word: str) -> np.ndarray:
    mask = np.zeros(26, dtype=bool)
    for ch in set(word):
        mask[ord(ch) - 97] = True
    return mask


def score_pair(
    first: str,
    second: str,
    answer_codes: np.ndarray,
    answer_counts: np.ndarray,
    masks: np.ndarray,
    distinct_counts: np.ndarray,
) -> dict:
    pair_mask = word_mask(first) | word_mask(second)
    patterns_first = pattern_codes(encode([first])[0], answer_codes, answer_counts)
    patterns_second = pattern_codes(encode([second])[0], answer_codes, answer_counts)
    combined = patterns_first * PATTERN_SPACE + patterns_second
    _, counts = np.unique(combined, return_counts=True)
    total = answer_codes.shape[0]
    spot = float(((masks & pair_mask).sum(axis=1) / distinct_counts).mean())
    return {
        "first": first,
        "second": second,
        "expected_remaining": round(
            float((counts.astype(np.float64) ** 2).sum() / total), 2
        ),
        "solved_on_two_pct": round(100 * float((counts == 1).sum()) / total, 2),
        "spot_rate_pct": round(100 * spot, 1),
    }


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    allowed = load_words(ALLOWED_PATH)
    pool_words = sorted(set(answers) | set(allowed))
    answer_codes = encode(answers)
    answer_counts = letter_counts(answer_codes)
    masks = letter_masks(answers)
    distinct_counts = masks.sum(axis=1)

    first_pool = [
        row["word"]
        for row in rank_openers(pool_words, answers, FIRST_GUESS_POOL)["top"]
    ]
    seen = set()
    scored = []
    for first in first_pool:
        first_mask = word_mask(first)
        for second_index, second in enumerate(answers):
            if (masks[second_index] & first_mask).any():
                continue
            pair_key = tuple(sorted((first, second)))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            scored.append(
                score_pair(
                    pair_key[0],
                    pair_key[1],
                    answer_codes,
                    answer_counts,
                    masks,
                    distinct_counts,
                )
            )

    scored.sort(key=lambda row: row["expected_remaining"])
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "coverage.json").write_text(json.dumps(scored[:200], indent=2))

    lines = [
        "# Disjoint opener pairs (guess 2 shares no letters with guess 1)",
        "",
        "| # | Pair | Expected remaining after 2 | Spot rate |",
        "|---|---|---|---|",
    ]
    for rank, row in enumerate(scored[:TOP_PAIRS], start=1):
        lines.append(
            f"| {rank} | {row['first'].upper()} + {row['second'].upper()} "
            f"| {row['expected_remaining']} | {row['spot_rate_pct']}% |"
        )
    (RESULTS_DIR / "coverage.md").write_text("\n".join(lines) + "\n")

    print(f"Scored {len(scored)} disjoint pairs.")
    for row in scored[:TOP_PAIRS]:
        print(
            f"  {row['first'].upper():6} + {row['second'].upper():6} "
            f"remaining {row['expected_remaining']:6.2f}  spot {row['spot_rate_pct']}%"
        )


if __name__ == "__main__":
    main()
