# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Guess-3 tree for SOARE + CLINT, branched on hit count (0-5).

A "hit" = a letter from the 10 tested that is green or yellow in the
feedback. Hit count fixes the candidate pool; the recommended word is the
one that leaves the fewest expected candidates, and its action label says
what that word is:

  * Candidate  — the word is still in the pattern's candidate pool.
  * Split word — the word is not in the pool but reuses a letter already hit.
  * Burn word  — the word is not in the pool and tests only fresh letters.

Expected candidates left after a guess = sum over feedback groups of
group_size squared / pool size. The feedback used here is standard Wordle
feedback (greens first, then yellows left to right, each copy consumed once);
``analyze.pattern_codes`` over-marks yellow for guesses with a repeated
letter, so this module scores guesses locally.
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
ANSWERS_PATH = ROOT / "data" / "answers.txt"
RESULTS_DIR = ROOT / "results"

PAIR = ("soare", "clint")
STATE_CHARS = {0: "X", 1: "Y", 2: "G"}
TOP_N = 3
ALPHABET = 26

RULE = (
    "Count your hits to find the candidate pool, then play the word that "
    "leaves the fewest expected candidates: a candidate if that word is still "
    "possible, otherwise a split word that reuses a hit letter or a burn word "
    "that tests only fresh letters."
)

ACTION_ORDER = ["Candidate", "Split word", "Burn word"]


def load_words(path: Path) -> list[str]:
    return [
        line.strip().lower() for line in path.read_text().splitlines() if line.strip()
    ]


def encode(words: list[str]) -> np.ndarray:
    return np.array([[ord(ch) - 97 for ch in word] for word in words], dtype=np.int8)


def letter_counts(codes: np.ndarray) -> np.ndarray:
    counts = np.zeros((codes.shape[0], ALPHABET), dtype=np.int16)
    for position in range(codes.shape[1]):
        counts[np.arange(codes.shape[0]), codes[:, position]] += 1
    return counts


def pattern_codes(
    guess: np.ndarray, answer_codes: np.ndarray, answers_letter_counts: np.ndarray
) -> np.ndarray:
    """Standard Wordle feedback (base-3 code per answer) for one guess.

    Unlike ``analyze.pattern_codes`` this consumes each yellow copy, so a
    guess with a repeated letter cannot mark more yellows than the answer
    actually contains.
    """
    green = answer_codes == guess
    state = np.where(green, 2, 0).astype(np.int8)
    available = answers_letter_counts.astype(np.int16).copy()
    for position in range(5):
        letter = guess[position]
        available[green[:, position], letter] -= 1
    for position in range(5):
        letter = guess[position]
        yellow = (~green[:, position]) & (available[:, letter] > 0)
        state[yellow, position] = 1
        available[yellow, letter] -= 1
    return state @ (3 ** np.arange(5))


def sum_sq(
    guess: np.ndarray, answer_codes: np.ndarray, answers_letter_counts: np.ndarray
) -> int:
    """Integer numerator of expected candidates left (same denominator per pool)."""
    patterns = pattern_codes(guess, answer_codes, answers_letter_counts)
    _, counts = np.unique(patterns, return_counts=True)
    return int((counts.astype(np.int64) ** 2).sum())


def decode_pattern(code: int) -> str:
    chars = []
    for _ in range(5):
        chars.append(STATE_CHARS[code % 3])
        code //= 3
    return "".join(chars)


def hits_for(p1: int, p2: int) -> int:
    present = set()
    for guess, pat in [(PAIR[0], p1), (PAIR[1], p2)]:
        for pos in range(5):
            if (pat // (3**pos)) % 3 > 0:
                present.add(guess[pos])
    return len(present)


def hit_letters(p1: int, p2: int) -> set[str]:
    letters = set()
    for guess, pat in [(PAIR[0], p1), (PAIR[1], p2)]:
        for pos in range(5):
            if (pat // (3**pos)) % 3 > 0:
                letters.add(guess[pos])
    return letters


def label_for(word: str, in_pool: bool, letters: set[str]) -> str:
    if in_pool:
        return "Candidate"
    return "Split word" if set(word) & letters else "Burn word"


def best_word(
    answers: list[str],
    answer_codes: np.ndarray,
    pool: list[str],
    pool_codes: np.ndarray,
    pool_counts: np.ndarray,
) -> tuple[str, int, bool]:
    """Word minimising expected remaining; ties prefer a remaining candidate."""
    in_pool = set(pool)
    best = None
    for j, word in enumerate(answers):
        sq = sum_sq(answer_codes[j], pool_codes, pool_counts)
        key = (sq, 0 if word in in_pool else 1, word)
        if best is None or key < best[0]:
            best = (key, word, sq)
    _, word, sq = best
    return word, sq, word in in_pool


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    ans_codes = encode(answers)
    ans_counts = letter_counts(ans_codes)

    buckets: dict[int, dict[tuple[int, int], list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for i, word in enumerate(answers):
        p1 = int(
            pattern_codes(
                encode([PAIR[0]])[0], ans_codes[i : i + 1], ans_counts[i : i + 1]
            )[0]
        )
        p2 = int(
            pattern_codes(
                encode([PAIR[1]])[0], ans_codes[i : i + 1], ans_counts[i : i + 1]
            )[0]
        )
        buckets[hits_for(p1, p2)][(p1, p2)].append(word)

    rows = []
    for h in sorted(buckets):
        patterns = buckets[h]
        total = sum(len(v) for v in patterns.values())
        cand_sizes = [len(v) for v in patterns.values()]

        top_patterns = []
        for (p1, p2), words in sorted(
            patterns.items(),
            key=lambda kv: (
                -len(kv[1]),
                decode_pattern(kv[0][0]),
                decode_pattern(kv[0][1]),
            ),
        )[:TOP_N]:
            pool_codes = encode(words)
            pool_counts = letter_counts(pool_codes)
            word, sq, in_pool = best_word(
                answers, ans_codes, words, pool_codes, pool_counts
            )
            action = label_for(word, in_pool, hit_letters(p1, p2))
            candidate_scores = {
                w: sum_sq(encode([w])[0], pool_codes, pool_counts) for w in words
            }
            best_candidate = min(candidate_scores, key=lambda w: (candidate_scores[w], w))
            best_candidate_sq = candidate_scores[best_candidate]
            top_patterns.append(
                {
                    "g1": PAIR[0].upper(),
                    "g1_pattern": decode_pattern(p1),
                    "g2": PAIR[1].upper(),
                    "g2_pattern": decode_pattern(p2),
                    "candidates": len(words),
                    "action": action,
                    "in_pool": in_pool,
                    "guess3": word,
                    "expected_remaining": round(sq / len(words), 2),
                    "best_candidate": best_candidate,
                    "best_candidate_remaining": round(best_candidate_sq / len(words), 2),
                }
            )

        actions = [tp["action"] for tp in top_patterns]
        rows.append(
            {
                "hits": h,
                "share_pct": round(100 * total / len(answers), 1),
                "answers": total,
                "patterns": len(patterns),
                "avg_candidates": round(sum(cand_sizes) / len(cand_sizes), 1),
                "max_candidates": max(cand_sizes),
                "strategy": top_patterns[0]["action"],
                "actions": [a for a in ACTION_ORDER if a in actions],
                "rule": RULE,
                "top_patterns": top_patterns,
            }
        )

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "hit_tree.json").write_text(json.dumps(rows, indent=2))

    lines = [
        f"# Guess-3 tree after {'+'.join(PAIR).upper()}, branched on hit count",
        "",
        "A hit = a tested letter that shows green or yellow.",
        "",
        f"**The rule:** {RULE}",
        "",
        "| Hits | Share | Patterns | Avg left | Max left | Actions in largest pools |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['hits']} | {row['share_pct']}% | {row['patterns']} "
            f"| {row['avg_candidates']} | {row['max_candidates']} "
            f"| {', '.join(row['actions'])} |"
        )

    for row in rows:
        lines.append("")
        lines.append(f"## {row['hits']} hits")
        lines.append("")
        lines.append(
            f"{row['share_pct']}% of games, {row['patterns']} patterns, "
            f"avg {row['avg_candidates']} candidates "
            f"(largest pools shown, {len(row['top_patterns'])} of them)"
        )
        lines.append("")
        lines.append(
            "| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Action | Guess 3 | Left |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for tp in row["top_patterns"]:
            lines.append(
                f"| {tp['g1']} | {tp['g1_pattern']} | {tp['g2']} | {tp['g2_pattern']} "
                f"| {tp['candidates']} | {tp['action']} | {tp['guess3'].upper()} "
                f"| {tp['expected_remaining']} |"
            )

    (RESULTS_DIR / "hit_tree.md").write_text("\n".join(lines) + "\n")

    for row in rows:
        print(
            f"  {row['hits']} hits  {row['share_pct']:5.1f}%  "
            f"patterns {row['patterns']:3}  avg {row['avg_candidates']:4}  "
            f"max {row['max_candidates']:3}  -> {', '.join(row['actions'])}"
        )


if __name__ == "__main__":
    main()
