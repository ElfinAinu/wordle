# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""What full vowel coverage costs, and what it buys.

`vowel_tree.py` branches the guess-3 decision on which of the *tested* vowels
(A E I O) hit, leaving U and Y undecided. This script answers the follow-up the
poster's section IX needs: if the feedback decides all six of A E I O U Y, how
do the one-vowel branches split, and is spending a guess on that coverage worth
it?

Three measurements, all over the 2,309 committed answers in data/answers.txt:

  * full coverage  - the branch is the exact vowel set, all six decided.
  * partial coverage - the branch is which of A E I O shows, U and Y unknown
    (what SOARE + CLINT gives you). Reported for the same single-vowel read so
    the two can be compared directly.
  * the cost - average guesses for a fixed opening of two coverage words versus
    three, both continued by the same minimax policy.

The cost reuses `simulate_method.simulate` rather than restating its policy, so
it needs the hit_tree import chain to be healthy.

Outputs results/full_coverage.md and results/full_coverage.json. Regenerating
twice produces identical files.
"""

import json
from collections import Counter
from pathlib import Path

from analyze import (
    ALLOWED_PATH,
    ANSWERS_PATH,
    RESULTS_DIR,
    encode,
    letter_counts,
    load_words,
    score_guess,
)

ROOT = Path(__file__).parent

# Every vowel the poster's three coverage words decide: SOARE gives A O E,
# CLINT gives I, DUMPY gives U and Y.
FULL_VOWELS = set("aeiouy")
# What SOARE + CLINT decide on their own; U and Y stay unknown.
PARTIAL_VOWELS = set("aeio")

# The two conventions a reader might count under. `aeiou` is the plain reading;
# `aeiouy` is the one section IX uses, since DUMPY is played for Y as well.
VOWEL_SETS = {"aeiou": set("aeiou"), "aeiouy": set("aeiouy")}
MAX_VOWELS = 5

TWO_OPENER_OPENING = ("soare", "clint")
THREE_OPENER_OPENING = ("soare", "clint", "dumpy")


def share(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def vowel_counts(pools: dict[str, list[str]]) -> dict:
    """How many vowels each word carries, per pool and per counting convention."""
    measured = {}
    for label, words in pools.items():
        total = len(words)
        by_convention = {}
        for name, vowels in VOWEL_SETS.items():
            tally = Counter(sum(1 for ch in word if ch in vowels) for word in words)
            more_than_two = sum(n for count, n in tally.items() if count > 2)
            by_convention[name] = {
                "rows": [
                    {
                        "vowels": count,
                        "words": tally.get(count, 0),
                        "share_pct": share(tally.get(count, 0), total),
                    }
                    for count in range(MAX_VOWELS + 1)
                ],
                "more_than_two": more_than_two,
                "more_than_two_pct": share(more_than_two, total),
            }
        measured[label] = {
            "words": total,
            "by_vowel_set": by_convention,
        }
    return measured


def present_vowels(word: str, vowels: set[str]) -> frozenset[str]:
    return frozenset(ch for ch in word if ch in vowels)


def best_guess(pool: list[str], guess_pool: list[str], pool_codes, guess_codes):
    """The guess minimising expected candidates remaining over `pool`."""
    counts = letter_counts(pool_codes)
    best = min(
        (
            (guess, *score_guess(guess_codes[index], pool_codes, counts))
            for index, guess in enumerate(guess_pool)
        ),
        key=lambda row: row[2],
    )
    return {"guess": best[0], "entropy": round(best[1], 3), "left": round(best[2], 2)}


def single_vowel_branches(
    words: list[str], vowels: set[str], guess_pool: list[str], guess_codes
) -> dict:
    """Per-vowel stats for the branches that show exactly one vowel."""
    total = len(words)
    groups: dict[str, list[str]] = {}
    for word in words:
        present = present_vowels(word, vowels)
        if len(present) == 1:
            groups.setdefault(next(iter(present)), []).append(word)

    rows = []
    for vowel in sorted(groups):
        branch = groups[vowel]
        size = len(branch)
        vowel_repeats = sum(1 for word in branch if Counter(word)[vowel] > 1)
        consonant_repeats = sum(
            1 for word in branch if Counter(word)[vowel] == 1 and len(set(word)) < 5
        )
        pick = best_guess(branch, guess_pool, encode(branch), guess_codes)
        rows.append(
            {
                "vowel": vowel.upper(),
                "answers": size,
                "share_pct": share(size, total),
                "vowel_repeats": vowel_repeats,
                "vowel_repeat_pct": share(vowel_repeats, size),
                "consonant_repeats": consonant_repeats,
                "consonant_repeat_pct": share(consonant_repeats, size),
                "nothing_repeats_pct": share(
                    size - vowel_repeats - consonant_repeats, size
                ),
                "any_repeat_pct": share(vowel_repeats + consonant_repeats, size),
                "next_guess": pick["guess"].upper(),
                "next_guess_left": pick["left"],
            }
        )

    shapes = Counter(len(present_vowels(word, vowels)) for word in words)
    return {
        "vowels_decided": "".join(sorted(vowels)),
        "answers": total,
        "shape_counts": {
            "no_vowel": shapes.get(0, 0),
            "one_vowel": shapes.get(1, 0),
            "two_or_more": sum(n for k, n in shapes.items() if k >= 2),
        },
        "one_vowel_pct": share(shapes.get(1, 0), total),
        "rows": rows,
    }


def coverage_cost(words: list[str]) -> dict:
    """Average guesses for a fixed two- and three-word opening."""
    import simulate_method

    measured = {}
    for label, openers in (
        ("two_openers", TWO_OPENER_OPENING),
        ("three_openers", THREE_OPENER_OPENING),
    ):
        simulate_method.OPENERS = openers
        result = simulate_method.simulate(words)
        measured[label] = {
            "openers": [word.upper() for word in openers],
            "average_guesses": result["average_guesses"],
            "worst_case_guesses": result["worst_case_guesses"],
            "six_or_fail_pct": result["six_or_fail_pct"],
        }

    extra = (
        measured["three_openers"]["average_guesses"]
        - measured["two_openers"]["average_guesses"]
    )
    return {
        "two_openers": measured["two_openers"],
        "three_openers": measured["three_openers"],
        "extra_guesses": round(extra, 4),
        "note": (
            "Both openings are continued by simulate_method's "
            "expected-candidates-minimising policy over data/answers.txt."
        ),
    }


def analyse(words: list[str]) -> dict:
    guess_pool = words
    guess_codes = encode(guess_pool)
    full = single_vowel_branches(words, FULL_VOWELS, guess_pool, guess_codes)
    partial = single_vowel_branches(words, PARTIAL_VOWELS, guess_pool, guess_codes)
    all_valid = sorted(set(words) | set(load_words(ALLOWED_PATH)))
    return {
        "universe": {
            "path": "data/answers.txt",
            "words": len(words),
            "description": "the committed Wordle answer list",
        },
        "coverage_words": [word.upper() for word in THREE_OPENER_OPENING],
        "full": full,
        "partial": partial,
        "vowel_counts": vowel_counts(
            {"answers": words, "all_valid": all_valid}
        ),
        "cost": coverage_cost(words),
    }


def write_markdown(stats: dict, path: Path) -> None:
    full = stats["full"]
    partial = stats["partial"]
    cost = stats["cost"]
    lines = [
        "# Full vowel coverage: what it costs and what it buys",
        "",
        f"Universe: {stats['universe']['path']} ({stats['universe']['words']} answers). "
        f"Coverage words: {' + '.join(stats['coverage_words'])}.",
        "",
        "A *branch* is the set of answers consistent with the vowel feedback. "
        "Every share names its own denominator: the branch's answer count.",
        "",
        "## With all six vowels decided",
        "",
        f"Decided: {full['vowels_decided']}. No answer has zero of them "
        f"({full['shape_counts']['no_vowel']}), so the first vowel is always found. "
        f"Exactly one shows in {full['one_vowel_pct']}% of games.",
        "",
        "| only this shows | answers | share | vowel repeats | consonant repeats | nothing repeats | next guess | left |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in full["rows"]:
        lines.append(
            f"| {row['vowel']} | {row['answers']} | {row['share_pct']}% | "
            f"{row['vowel_repeat_pct']}% | {row['consonant_repeat_pct']}% | "
            f"{row['nothing_repeats_pct']}% | {row['next_guess']} | {row['next_guess_left']} |"
        )
    lines.append("")

    lines.append("## The same read without U and Y decided")
    lines.append("")
    lines.append(
        f"Decided: {partial['vowels_decided']} (SOARE + CLINT). U and Y are still "
        "unknown, so each branch is larger."
    )
    lines.append("")
    lines.append(
        "| only this shows | answers | share | vowel repeats | next guess | left |"
    )
    lines.append("|---|---|---|---|---|---|")
    for row in partial["rows"]:
        lines.append(
            f"| {row['vowel']} | {row['answers']} | {row['share_pct']}% | "
            f"{row['vowel_repeat_pct']}% | {row['next_guess']} | {row['next_guess_left']} |"
        )
    lines.append("")

    counts = stats["vowel_counts"]
    pools_in_order = ("answers", "all_valid")
    lines.append("## Vowels per word")
    lines.append("")
    lines.append(
        "Share of each pool by vowel count, under both counting conventions. "
        "`aeiouy` is the one section IX uses, since DUMPY is played for Y as well as U."
    )
    lines.append("")
    for name in ("aeiou", "aeiouy"):
        lines.append(f"Counting `{name}`:")
        lines.append("")
        lines.append(
            "| vowels | "
            + " | ".join(f"{label} ({counts[label]['words']})" for label in pools_in_order)
            + " |"
        )
        lines.append("|" + "---|" * (len(pools_in_order) + 1))
        for count in range(MAX_VOWELS + 1):
            cells = []
            for label in pools_in_order:
                row = counts[label]["by_vowel_set"][name]["rows"][count]
                cells.append(f"{row['words']} ({row['share_pct']}%)")
            lines.append(f"| {count} | " + " | ".join(cells) + " |")
        summary = []
        for label in pools_in_order:
            block = counts[label]["by_vowel_set"][name]
            summary.append(f"{block['more_than_two']} ({block['more_than_two_pct']}%)")
        lines.append("| **3 or more** | " + " | ".join(summary) + " |")
        lines.append("")

    lines.append("## What coverage costs")
    lines.append("")
    lines.append("| opening | average guesses | worst case | six or fail |")
    lines.append("|---|---|---|---|")
    for key in ("two_openers", "three_openers"):
        row = cost[key]
        lines.append(
            f"| {' + '.join(row['openers'])} | {row['average_guesses']:.4f} | "
            f"{row['worst_case_guesses']} | {row['six_or_fail_pct']}% |"
        )
    lines.append("")
    lines.append(
        f"A third coverage word costs {cost['extra_guesses']:.2f} guesses a game on "
        f"average. {cost['note']}"
    )
    lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    words = load_words(ANSWERS_PATH)
    stats = analyse(words)

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "full_coverage.json").write_text(json.dumps(stats, indent=2))
    write_markdown(stats, RESULTS_DIR / "full_coverage.md")

    for row in stats["full"]["rows"]:
        print(
            f"  only {row['vowel']}: {row['answers']:4} answers, vowel repeats "
            f"{row['vowel_repeat_pct']:5}%, next {row['next_guess']:6} "
            f"left {row['next_guess_left']}"
        )
    counts = stats["vowel_counts"]
    for label in ("answers", "all_valid"):
        for name in ("aeiou", "aeiouy"):
            block = counts[label]["by_vowel_set"][name]
            print(
                f"  {label:10} counting {name:7}: 3 or more vowels "
                f"{block['more_than_two']:5} ({block['more_than_two_pct']}%)"
            )
    print(
        f"coverage cost: {stats['cost']['two_openers']['average_guesses']:.4f} -> "
        f"{stats['cost']['three_openers']['average_guesses']:.4f} "
        f"(+{stats['cost']['extra_guesses']:.2f})"
    )
    print("Wrote results/full_coverage.json and results/full_coverage.md")


if __name__ == "__main__":
    main()
