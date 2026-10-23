#!/usr/bin/env python3
"""Ticket 06 check: the taught-method simulation and its feedback function.

Validates hit_tree.pattern_codes against a hand-written Wordle reference on
duplicated guess letters, duplicated answer letters, and letters absent from
the guess, then asserts every acceptance criterion in
.scratch/poster-fixes/issues/06-simulate-method.md against
results/simulate_method.{json,md}.

Run: uv run --with numpy python .scratch/poster-fixes/checks/06-simulate-method.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import hit_tree

ANSWERS_PATH = ROOT / "data" / "answers.txt"
RESULTS_DIR = ROOT / "results"


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


def old_bug_feedback(guess: str, answer: str) -> str:
    """analyze.pattern_codes' old behaviour: yellows ignore assigned copies."""
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


def validate_feedback(answers: list[str]) -> None:
    explicit_cases = [
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
    for guess, answer, expected in explicit_cases:
        got_reference = reference_feedback(guess, answer)
        assert got_reference == expected, (
            f"reference self-check failed for {guess}/{answer}: "
            f"{got_reference} != {expected}"
        )
        got = hit_tree.decode_pattern(
            int(
                hit_tree.pattern_codes(
                    hit_tree.encode([guess])[0],
                    hit_tree.encode([answer]),
                    hit_tree.letter_counts(hit_tree.encode([answer])),
                )[0]
            )
        )
        assert got == expected, (
            f"hit_tree.pattern_codes {guess}/{answer}: {got} != {expected}"
        )

    all_codes = hit_tree.encode(answers)
    all_counts = hit_tree.letter_counts(all_codes)
    tricky_guesses = ["reedy", "speed", "allee", "eerie", "sassy", "array", "civic"]
    for guess in tricky_guesses:
        guess_code = hit_tree.encode([guess])[0]
        for index, answer in enumerate(answers):
            got = hit_tree.decode_pattern(
                int(
                    hit_tree.pattern_codes(
                        guess_code,
                        all_codes[index : index + 1],
                        all_counts[index : index + 1],
                    )[0]
                )
            )
            want = reference_feedback(guess, answer)
            assert got == want, (
                f"feedback mismatch for {guess}/{answer}: {got} != {want}"
            )

    # The historical bug: reedy over-marked yellows on 612 of 2,309 answers.
    buggy = sum(
        old_bug_feedback("reedy", answer) != reference_feedback("reedy", answer)
        for answer in answers
    )
    assert buggy == 612, f"expected 612 old-bug answers for reedy, found {buggy}"


def check_results(answers: list[str]) -> None:
    result = json.loads((RESULTS_DIR / "simulate_method.json").read_text())
    markdown = (RESULTS_DIR / "simulate_method.md").read_text()
    total = len(answers)

    assert result["total_games"] == total == 2309
    assert result["method"]["openers"] == ["soare", "clint"]
    assert result["method"]["guess_3_rule"] == hit_tree.RULE
    assert result["method"]["feedback"] == "hit_tree.pattern_codes"
    assert "data/allowed.txt was not used" in result["method"]["guess_universe"]
    assert "no stronger" in result["method"]["substitutions"]

    distribution = {row["guess"]: row for row in result["guess_distribution"]}
    for guess in range(1, 7):
        assert guess in distribution, f"missing solve share for guess {guess}"
    solved_counts = {guess: distribution[guess]["count"] for guess in range(1, 7)}
    failed = result["failed_count"]
    assert sum(solved_counts.values()) + failed == total
    assert distribution[1]["count"] == 0 and distribution[2]["count"] == 0

    measured_average = sum(guess * count for guess, count in solved_counts.items()) / (
        total - failed
    )
    assert abs(measured_average - result["average_guesses"]) < 0.0001
    assert result["average_guesses"] == 3.6146
    assert (
        result["worst_case_guesses"]
        == max(guess for guess, count in solved_counts.items() if count)
        == 6
    )
    assert result["six_or_fail_count"] == solved_counts[6] + failed == 1
    assert result["six_or_fail_pct"] == 0.04
    assert result["failed_count"] == 0

    # Measured distribution is part of the evidence; a policy drift should fail.
    assert solved_counts == {1: 0, 2: 0, 3: 1004, 4: 1192, 5: 112, 6: 1}
    assert abs(sum(row["share_pct"] for row in distribution.values()) - 100) < 0.1

    assert "3.61" in markdown
    assert "| Worst case | 6 guesses |" in markdown
    assert "| Solved on six or failed | 1 (0.04%) |" in markdown
    assert "| Failed (not solved within 12) | 0 (0.00%) |" in markdown
    assert "JOKER" in markdown

    hard = result["hard_paths"]
    assert len(hard) == 1 and hard[0]["answer"] == "joker" and hard[0]["guesses"] == 6
    assert hard[0]["path"] == [
        "SOARE XGXYY",
        "CLINT XXXXX",
        "WIMPY XXXXX",
        "ROVER XGXGG",
        "BOXER XGXGG",
        "JOKER GGGGG",
    ]


def main() -> int:
    answers = [
        word.strip().lower()
        for word in ANSWERS_PATH.read_text().splitlines()
        if word.strip()
    ]
    try:
        validate_feedback(answers)
        check_results(answers)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS")
    print(
        "  feedback: hit_tree.pattern_codes matches reference on tricky and full-pool cases"
    )
    print(
        "  average 3.6146 guesses, worst 6, solved on six or failed 1 of 2309 (0.04%)"
    )
    print("  solve shares per guess: 0 / 0 / 1004 / 1192 / 112 / 1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
