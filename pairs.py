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
    encode,
    letter_counts,
    load_words,
    pattern_codes,
    rank_openers,
)

STATE_CHARS = {0: "X", 1: "Y", 2: "G"}
POSITION_WEIGHTS = 3 ** np.arange(5)
TOP_OPENERS = 8


def decode_pattern(code: int) -> str:
    digits = []
    for _ in range(5):
        digits.append(code % 3)
        code //= 3
    return "".join(STATE_CHARS[d] for d in digits)


def group_candidates(opener: str, answer_codes: np.ndarray, answer_counts: np.ndarray):
    patterns = pattern_codes(encode([opener])[0], answer_codes, answer_counts)
    unique, inverse = np.unique(patterns, return_inverse=True)
    return [
        (int(code), answer_codes[inverse == gid]) for gid, code in enumerate(unique)
    ]


def expected_remaining_per_guess(
    pool_codes: np.ndarray, candidates: np.ndarray
) -> np.ndarray:
    """Expected remaining candidates after each pool guess, vectorized over the pool."""
    pool_onehot = np.eye(26, dtype=np.int8)[pool_codes]
    cand_onehot = np.eye(26, dtype=np.int8)[candidates]
    green_match = np.einsum("ipc,jpc->ijc", pool_onehot, cand_onehot, dtype=np.int8)
    cand_letter_counts = letter_counts(candidates)

    pattern = np.zeros((pool_codes.shape[0], candidates.shape[0]), dtype=np.int32)
    for position in range(5):
        pool_letter = pool_codes[:, position]
        cand_letter = candidates[:, position]
        green = pool_letter[:, None] == cand_letter[None, :]
        yellow = (~green) & (
            cand_letter_counts.T[pool_letter]
            > green_match[
                np.arange(pool_codes.shape[0])[:, None],
                np.arange(candidates.shape[0])[None, :],
                pool_letter[:, None],
            ]
        )
        pattern += (
            np.where(green, 2, np.where(yellow, 1, 0)) * POSITION_WEIGHTS[position]
        )

    sorted_patterns = np.sort(pattern, axis=1)
    segment_start = np.empty_like(sorted_patterns, dtype=bool)
    segment_start[:, 0] = True
    segment_start[:, 1:] = sorted_patterns[:, 1:] != sorted_patterns[:, :-1]
    starts = np.flatnonzero(segment_start)
    ends = np.append(starts[1:], sorted_patterns.size)
    counts = ends - starts
    row_of_segment = starts // sorted_patterns.shape[1]
    sums = np.bincount(row_of_segment, weights=counts.astype(np.float64) ** 2)
    return sums / sorted_patterns.shape[1]


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
        remaining = expected_remaining_per_guess(pool_codes, candidates)
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
