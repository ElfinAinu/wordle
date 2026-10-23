# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Guess-3 path tree for SOARE + CLINT, branched on which tested vowels hit.

Tested vowels: A E I O (U is untested by the pair). Each branch = the set
of tested vowels present in the answer. Per branch: share of games,
candidate count, and the max-entropy guess 3 over those candidates.
"""

import json

from analyze import (
    ANSWERS_PATH,
    RESULTS_DIR,
    encode,
    letter_counts,
    load_words,
    score_guess,
)

TESTED_VOWELS = "aeio"
PAIR = ("soare", "clint")


def branch_key(word: str) -> str:
    present = [v for v in TESTED_VOWELS if v in word]
    return "".join(present).upper() or "NONE"


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    guess_pool = answers
    pool_codes = encode(guess_pool)

    groups: dict[str, list[str]] = {}
    for word in answers:
        groups.setdefault(branch_key(word), []).append(word)

    branches = []
    for key, words in groups.items():
        codes = encode(words)
        counts = letter_counts(codes)
        best_word, best_entropy, best_remaining = min(
            (
                (guess, *score_guess(pool_codes[i], codes, counts))
                for i, guess in enumerate(guess_pool)
            ),
            key=lambda row: row[2],
        )
        branches.append(
            {
                "vowels": key,
                "share_pct": round(100 * len(words) / len(answers), 1),
                "candidates": len(words),
                "guess3": best_word,
                "expected_remaining": round(best_remaining, 2),
                "universe": "data/answers.txt (2,309 past answers)",
                "pair": list(PAIR),
            }
        )

    branches.sort(key=lambda row: -row["share_pct"])
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "vowel_tree.json").write_text(json.dumps(branches, indent=2))

    lines = [
        f"# Guess-3 tree after {'+'.join(PAIR).upper()}, branched on vowel hits",
        "",
        "Candidates: 2,309 past answers (`data/answers.txt`).",
        "",
        "| Vowels hit | Share | Candidates | Guess 3 | Left after |",
        "|---|---|---|---|---|",
    ]
    for row in branches:
        lines.append(
            f"| {row['vowels']} | {row['share_pct']}% | {row['candidates']} "
            f"| {row['guess3'].upper()} | {row['expected_remaining']} |"
        )
    (RESULTS_DIR / "vowel_tree.md").write_text("\n".join(lines) + "\n")

    for row in branches:
        print(
            f"  {row['vowels']:5} {row['share_pct']:5.1f}%  cands {row['candidates']:4} "
            f"-> {row['guess3'].upper():6} left {row['expected_remaining']}"
        )


if __name__ == "__main__":
    main()
