# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Rank opener pairs and emit a correctness tree for the best opener.

Tree: opener -> (greens, yellows) group -> exact per-letter pattern
(G/Y/X) -> best adaptive second guess.
"""

import json
from pathlib import Path

import numpy as np

from analyze import (
    ALLOWED_PATH,
    ANSWERS_PATH,
    RESULTS_DIR,
    decode_pattern,
    encode,
    letter_counts,
    load_words,
    pattern_codes,
    rank_openers,
    sum_sq_batch,
)

TOP_OPENERS = 8


def group_candidates(opener: str, answer_codes: np.ndarray, answer_counts: np.ndarray):
    patterns = pattern_codes(encode([opener])[0], answer_codes, answer_counts)
    unique, inverse = np.unique(patterns, return_inverse=True)
    return [
        (int(code), answer_codes[inverse == gid]) for gid, code in enumerate(unique)
    ]


def expected_remaining_per_guess(
    pool_codes: np.ndarray, candidates: np.ndarray, candidate_counts: np.ndarray
) -> np.ndarray:
    """Expected remaining candidates after each pool guess."""
    sums = sum_sq_batch(pool_codes, candidates, candidate_counts)
    return sums.astype(np.float64) / candidates.shape[0]


def analyze_opener(
    opener: str,
    answer_codes: np.ndarray,
    answer_counts: np.ndarray,
    pool_codes: np.ndarray,
    pool_words: list[str],
    want_tree: bool,
):
    groups = group_candidates(opener, answer_codes, answer_counts)
    total = answer_codes.shape[0]
    opener_index = pool_words.index(opener)

    expected_after_two = 0.0
    solved_on_two = 0.0
    tree = []
    for code, candidates in groups:
        share = candidates.shape[0] / total
        if candidates.shape[0] == 1:
            solved_on_two += share
            expected_after_two += share
            continue
        remaining = expected_remaining_per_guess(
            pool_codes, candidates, letter_counts(candidates)
        )
        remaining[opener_index] = np.inf
        best = int(np.argmin(remaining))
        expected_after_two += share * float(remaining[best])
        if want_tree:
            tree.append(
                {
                    "pattern": decode_pattern(code),
                    "candidates": int(candidates.shape[0]),
                    "share_pct": round(100 * share, 2),
                    "best_second": pool_words[best],
                    "expected_remaining": round(float(remaining[best]), 2),
                }
            )

    result = {
        "opener": opener,
        "expected_remaining_after_two": round(expected_after_two, 2),
        "solved_on_two_pct": round(100 * solved_on_two, 2),
        "universe": "data/answers.txt (2,309 past answers)",
        "second_guess_universe": (
            "all valid guesses (data/answers.txt + data/allowed.txt)"
        ),
    }
    if want_tree:
        tree.sort(key=lambda row: -row["candidates"])
        result["tree"] = tree
    return result


def write_tree_markdown(report: dict, path: Path) -> None:
    lines = [
        f"# Opener pair tree: {report['opener'].upper()}",
        "",
        f"Solved on guess 2: **{report['solved_on_two_pct']}%** of games. "
        f"Expected candidates left after guess 2: **{report['expected_remaining_after_two']}**.",
        "",
        "Candidates: 2,309 past answers (`data/answers.txt`). Second guesses:",
        "any valid guess (answers + `data/allowed.txt`). This scan's opener is",
        f"{report['opener'].upper()}, not the poster's fixed SOARE+CLINT pair.",
        "",
    ]
    groups: dict[tuple[int, int], list[dict]] = {}
    for row in report["tree"]:
        greens = row["pattern"].count("G")
        yellows = row["pattern"].count("Y")
        groups.setdefault((greens, yellows), []).append(row)

    lines.append(f"{report['opener'].upper()}")
    for (greens, yellows), rows in sorted(
        groups.items(), key=lambda kv: -sum(r["share_pct"] for r in kv[1])
    ):
        group_share = sum(r["share_pct"] for r in rows)
        lines.append(
            f"├─ {greens} green / {yellows} yellow — {group_share:.1f}% of games"
        )
        for row in rows:
            lines.append(
                f"│   └─ {row['pattern']} ({row['candidates']} candidates) "
                f"→ {row['best_second'].upper()} (leaves ~{row['expected_remaining']})"
            )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    allowed = load_words(ALLOWED_PATH)
    pool_words = sorted(set(answers) | set(allowed))
    answer_codes = encode(answers)
    answer_counts = letter_counts(answer_codes)
    pool_codes = encode(pool_words)

    ranking = rank_openers(pool_words, answers, TOP_OPENERS)["top"]
    reports = [
        analyze_opener(
            row["word"],
            answer_codes,
            answer_counts,
            pool_codes,
            pool_words,
            want_tree=False,
        )
        for row in ranking
    ]
    reports.sort(key=lambda report: report["expected_remaining_after_two"])
    reports[0] = analyze_opener(
        reports[0]["opener"],
        answer_codes,
        answer_counts,
        pool_codes,
        pool_words,
        want_tree=True,
    )

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "pairs.json").write_text(json.dumps(reports, indent=2))
    write_tree_markdown(reports[0], RESULTS_DIR / "pairs.md")

    print("Opener pair ranking (expected candidates left after optimal 2nd guess):")
    for report in reports:
        print(
            f"  {report['opener'].upper():6} {report['expected_remaining_after_two']:7.2f} "
            f"(solved on 2: {report['solved_on_two_pct']}%)"
        )
    print(
        f"Wrote results/pairs.json and results/pairs.md (tree for {reports[0]['opener'].upper()})"
    )


if __name__ == "__main__":
    main()
