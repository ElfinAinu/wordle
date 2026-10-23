#!/usr/bin/env python3
"""Regression check for the one shared Wordle feedback implementation.

Compares ``analyze.pattern_codes`` with an independent pure-Python reference
for every answer and a set of guesses that repeat a letter, and for
hand-written edge cases covering duplicated guess letters, duplicated answer
letters, greens that consume an answer copy, and letters absent from the
answer. It also pins the old implementation's known mismatch counts, so the
check fails if the shared function regresses.

Run: uv run --with numpy python tests/test_pattern_codes.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analyze
import hit_tree
import pairs

ANSWERS_PATH = ROOT / "data" / "answers.txt"

# Guesses that repeat a letter. The first three are the historical bug cases.
REPEATED_GUESSES = [
    "reedy",
    "eerie",
    "aback",
    "speed",
    "allee",
    "sassy",
    "array",
    "civic",
    "belle",
    "abbey",
    "geese",
    "radar",
]

# Old analyze.pattern_codes marked these many answers differently from the game.
OLD_MISMATCH_COUNTS = {"reedy": 612, "eerie": 454, "aback": 446}

HANDWRITTEN_CASES = [
    # duplicated guess letter, one answer copy
    ("reedy", "abase", "XYXXX"),
    ("reedy", "creed", "YYGYX"),
    # duplicated answer letters
    ("speed", "abide", "XXYXY"),
    ("allee", "apple", "GYXXG"),
    ("eerie", "geese", "YGXXG"),
    ("belle", "level", "XGYYY"),
    # unusual duplicated patterns
    ("sassy", "assay", "YYGXG"),
    ("array", "radar", "YYYGX"),
    ("civic", "vivid", "XGGGX"),
    # letters absent from the answer
    ("abbey", "zonal", "YXXXX"),
]


def reference_feedback(guess: str, answer: str) -> str:
    """Standard Wordle feedback: greens first, then yellows left to right."""
    result = ["X"] * 5
    used = [False] * 5
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = "G"
            used[i] = True
    for i in range(5):
        if result[i] == "G":
            continue
        for j in range(5):
            if not used[j] and answer[j] == guess[i]:
                result[i] = "Y"
                used[j] = True
                break
    return "".join(result)


def old_feedback(guess: str, answer: str) -> str:
    """The previous shared implementation: yellows ignore copies already used."""
    green = [guess[i] == answer[i] for i in range(5)]
    green_counts: dict[str, int] = {}
    for i, is_green in enumerate(green):
        if is_green:
            green_counts[guess[i]] = green_counts.get(guess[i], 0) + 1
    answer_counts: dict[str, int] = {}
    for letter in answer:
        answer_counts[letter] = answer_counts.get(letter, 0) + 1
    result = []
    for i in range(5):
        if green[i]:
            result.append("G")
        elif answer_counts.get(guess[i], 0) > green_counts.get(guess[i], 0):
            result.append("Y")
        else:
            result.append("X")
    return "".join(result)


def assert_single_implementation() -> None:
    assert hit_tree.pattern_codes is analyze.pattern_codes, (
        "hit_tree keeps a private feedback implementation"
    )
    assert hit_tree.sum_sq is analyze.sum_sq, "hit_tree keeps a private sum_sq"
    assert pairs.pattern_codes is analyze.pattern_codes, (
        "pairs keeps a private feedback implementation"
    )
    assert pairs.sum_sq_batch is analyze.sum_sq_batch, "pairs keeps a private sum_sq"


def assert_handwritten_cases() -> None:
    for guess, answer, expected in HANDWRITTEN_CASES:
        reference = reference_feedback(guess, answer)
        assert reference == expected, (
            f"reference self-check failed for {guess}/{answer}: "
            f"{reference} != {expected}"
        )
        got_code = analyze.pattern_codes(
            analyze.encode([guess])[0],
            analyze.encode([answer]),
            analyze.letter_counts(analyze.encode([answer])),
        )[0]
        got = analyze.decode_pattern(int(got_code))
        assert got == expected, f"shared feedback {guess}/{answer}: {got} != {expected}"


def assert_every_repeated_guess_over_all_answers(answers: list[str]) -> None:
    codes = analyze.encode(answers)
    counts = analyze.letter_counts(codes)
    for guess in REPEATED_GUESSES:
        guess_code = analyze.encode([guess])[0]
        got_codes = analyze.pattern_codes(guess_code, codes, counts)
        for index, answer in enumerate(answers):
            got = analyze.decode_pattern(int(got_codes[index]))
            want = reference_feedback(guess, answer)
            assert got == want, (
                f"feedback mismatch for {guess}/{answer}: {got} != {want}"
            )


def assert_old_implementation_fails(answers: list[str]) -> None:
    for guess, expected in OLD_MISMATCH_COUNTS.items():
        mismatches = sum(
            old_feedback(guess, answer) != reference_feedback(guess, answer)
            for answer in answers
        )
        assert mismatches == expected, (
            f"old implementation mismatches {mismatches} answers for {guess}, "
            f"expected {expected}"
        )


def main() -> int:
    answers = analyze.load_words(ANSWERS_PATH)
    assert_single_implementation()
    assert_handwritten_cases()
    assert_every_repeated_guess_over_all_answers(answers)
    assert_old_implementation_fails(answers)
    print(
        f"PASS: {len(HANDWRITTEN_CASES)} edge cases and "
        f"{len(REPEATED_GUESSES)} repeated-letter guesses x {len(answers)} answers "
        "match the reference; the old implementation is pinned to 612/454/446 "
        "mismatches."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
