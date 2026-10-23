# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Simulate the taught fixed-opening method over the full answer pool.

The policy is the one in results/hit_tree.md: play SOARE, then CLINT, then on
every later turn play the unguessed answer-list word that minimises expected
candidates left (sum of squared feedback-group sizes), preferring a word that
is still a candidate on ties. Guess words are restricted to data/answers.txt,
matching hit_tree.py; data/allowed.txt is not used.

Feedback comes from hit_tree.pattern_codes, which consumes yellow copies
correctly for guesses with repeated letters.
"""

import json
from collections import Counter
from functools import cache
from pathlib import Path

import numpy as np

import hit_tree

ROOT = Path(__file__).parent
ANSWERS_PATH = ROOT / "data" / "answers.txt"
RESULTS_DIR = ROOT / "results"
OPENERS = hit_tree.PAIR
PATTERN_SPACE = 3**5
GREEN_CODE = PATTERN_SPACE - 1
SEARCH_LIMIT = 12
RESULTS_STEM = "simulate_method"


def build_pattern_table(
    answer_codes: np.ndarray, answer_counts: np.ndarray
) -> np.ndarray:
    table = np.empty((len(answer_codes), len(answer_codes)), dtype=np.uint8)
    for index in range(len(answer_codes)):
        table[index] = hit_tree.pattern_codes(
            answer_codes[index], answer_codes, answer_counts
        )
    return table


def simulate(answers: list[str]) -> dict:
    answer_codes = hit_tree.encode(answers)
    answer_counts = hit_tree.letter_counts(answer_codes)
    total = len(answers)
    pattern_table = build_pattern_table(answer_codes, answer_counts)
    opener_patterns = np.array(
        [
            hit_tree.pattern_codes(
                hit_tree.encode([word])[0], answer_codes, answer_counts
            )
            for word in OPENERS
        ],
        dtype=np.uint8,
    )
    group_base = np.arange(total, dtype=np.int64)[:, None] * PATTERN_SPACE

    @cache
    def choose(pool_index: tuple[int, ...], used: tuple[int, ...]) -> int:
        pool = np.array(pool_index, dtype=np.int64)
        patterns = pattern_table[:, pool]
        keys = group_base + patterns
        counts = np.bincount(keys.ravel(), minlength=total * PATTERN_SPACE).reshape(
            total, PATTERN_SPACE
        )
        sum_squares = (counts.astype(np.int64) ** 2).sum(axis=1)
        if used:
            sum_squares[list(used)] = 10**18
        in_pool = np.ones(total, dtype=np.int8)
        in_pool[pool] = 0
        order = np.lexsort((np.arange(total), in_pool, sum_squares))
        return int(order[0])

    solved = Counter()
    hard_paths = []

    def walk(
        pool_index: tuple[int, ...],
        used: tuple[int, ...],
        depth: int,
        path: list[str],
    ) -> None:
        pool = np.array(pool_index, dtype=np.int64)
        if depth < len(OPENERS):
            patterns = opener_patterns[depth, pool]
            guess_name = OPENERS[depth]
        else:
            guess = choose(pool_index, used)
            patterns = pattern_table[guess, pool]
            guess_name = answers[guess]
            used = tuple(sorted(used + (guess,)))

        is_solved = patterns == GREEN_CODE
        solved_count = int(is_solved.sum())
        if solved_count:
            solved[depth + 1] += solved_count
            if depth + 1 >= 6:
                hard_paths.append(
                    {
                        "answer": answers[int(pool[is_solved][0])],
                        "guesses": depth + 1,
                        "path": path + [f"{guess_name.upper()} GGGGG"],
                    }
                )

        remaining = pool[~is_solved]
        if remaining.size == 0:
            return

        remaining_patterns = patterns[~is_solved]
        if depth + 1 >= SEARCH_LIMIT:
            solved["failed"] += int(remaining.size)
            for answer_index in remaining:
                hard_paths.append(
                    {
                        "answer": answers[int(answer_index)],
                        "guesses": None,
                        "path": path
                        + [
                            f"{guess_name.upper()} "
                            f"{hit_tree.decode_pattern(int(patterns[pool == answer_index][0]))}"
                        ],
                    }
                )
            return

        for code in np.unique(remaining_patterns):
            group = remaining[remaining_patterns == code]
            walk(
                tuple(int(index) for index in group),
                used,
                depth + 1,
                path + [f"{guess_name.upper()} {hit_tree.decode_pattern(int(code))}"],
            )

    walk(tuple(range(total)), (), 0, [])

    failed = solved["failed"]
    max_solved = max((guess for guess in solved if guess != "failed"), default=0)
    last_guess = max(6, max_solved)
    distribution = []
    cumulative = 0
    for guess in range(1, last_guess + 1):
        count = solved[guess]
        cumulative += count
        distribution.append(
            {
                "guess": guess,
                "count": count,
                "share_pct": round(100 * count / total, 2),
                "cumulative_pct": round(100 * cumulative / total, 2),
            }
        )

    average = sum(guess * count for guess, count in solved.items() if guess != "failed")
    average /= total - failed
    at_least_six = (
        sum(
            count for guess, count in solved.items() if guess != "failed" and guess >= 6
        )
        + failed
    )

    return {
        "method": {
            "openers": list(OPENERS),
            "guess_3_rule": hit_tree.RULE,
            "continuation": (
                "After guess 3 the same expected-candidates-minimising rule is "
                "applied each turn, excluding words already played."
            ),
            "guess_universe": (
                "data/answers.txt (2,309 words), the same pool hit_tree.py scores; "
                "data/allowed.txt was not used."
            ),
            "substitutions": (
                "None: no stronger solver or candidate-only policy was substituted. "
                "Later guesses reuse the guess-3 rule rather than playing an exact "
                "optimal policy."
            ),
            "feedback": "hit_tree.pattern_codes",
        },
        "total_games": total,
        "average_guesses": round(average, 4),
        "worst_case_guesses": max_solved if failed == 0 else None,
        "guess_distribution": distribution,
        "failed_count": failed,
        "failed_pct": round(100 * failed / total, 2),
        "six_or_fail_count": at_least_six,
        "six_or_fail_pct": round(100 * at_least_six / total, 2),
        "hard_paths": hard_paths,
    }


def write_markdown(result: dict, path: Path) -> None:
    method = result["method"]
    lines = [
        "# Simulated performance of the taught fixed-opening method",
        "",
        f"Policy: play **{method['openers'][0].upper()}**, then "
        f"**{method['openers'][1].upper()}**, then apply the guess-3 rule from "
        "`results/hit_tree.md` on every later turn.",
        "",
        f"> {method['guess_3_rule']}",
        "",
        f"- Feedback: `{method['feedback']}` (standard greens-first Wordle feedback; "
        "each yellow consumes one answer copy).",
        f"- Guess words: {method['guess_universe']}",
        f"- Continuation: {method['continuation']}",
        f"- Substitutions: {method['substitutions']}",
        "",
        "| Metric | Result |",
        "|---|---|",
        f"| Games | {result['total_games']} |",
        f"| Average guesses | {result['average_guesses']:.2f} |",
        f"| Worst case | {result['worst_case_guesses']} guesses |",
        f"| Solved on six or failed | {result['six_or_fail_count']} "
        f"({result['six_or_fail_pct']:.2f}%) |",
        f"| Failed (not solved within {SEARCH_LIMIT}) | {result['failed_count']} "
        f"({result['failed_pct']:.2f}%) |",
        "",
        "## Solve share by guess",
        "",
        "| Guess | Solved | Share | Cumulative |",
        "|---|---|---|---|",
    ]
    for row in result["guess_distribution"]:
        lines.append(
            f"| {row['guess']} | {row['count']} | {row['share_pct']:.2f}% "
            f"| {row['cumulative_pct']:.2f}% |"
        )
    lines.extend(
        [
            f"| Failed | {result['failed_count']} | {result['failed_pct']:.2f}% "
            f"| {round(100 * (result['total_games'] - result['failed_count']) / result['total_games'], 2):.2f}% |",
            "",
            "## Games needing six guesses or failing",
            "",
        ]
    )
    if result["hard_paths"]:
        lines.extend(
            [
                "| Answer | Guesses | Path |",
                "|---|---|---|",
            ]
        )
        for game in result["hard_paths"]:
            guesses = game["guesses"] if game["guesses"] is not None else "failed"
            lines.append(
                f"| {game['answer'].upper()} | {guesses} | {'; '.join(game['path'])} |"
            )
    else:
        lines.append("None.")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    answers = hit_tree.load_words(ANSWERS_PATH)
    result = simulate(answers)
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / f"{RESULTS_STEM}.json").write_text(json.dumps(result, indent=2))
    write_markdown(result, RESULTS_DIR / f"{RESULTS_STEM}.md")
    print(
        f"{result['total_games']} games, average {result['average_guesses']:.2f} "
        f"guesses, worst {result['worst_case_guesses']}, "
        f"six-or-fail {result['six_or_fail_count']} "
        f"({result['six_or_fail_pct']:.2f}%)"
    )


if __name__ == "__main__":
    main()
