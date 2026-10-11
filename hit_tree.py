# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Guess-3 tree for SOARE + CLINT, branched on hit count (0-5).

A "hit" = a letter from the 10 tested that is green or yellow in the
feedback. Hit count drives the guess-3 mode:

  0 hits -> test new letters (answer uses none of your 10)
  1-2    -> place known letters + test 1 new
  3-4    -> burn word to split remaining candidates
  5      -> solved

For each hit-count bucket we report share, pattern count, candidate
stats, and the top-3 most common feedback patterns with their best
guess 3 (max entropy over that pattern's candidates).
"""

import json
from collections import defaultdict

from analyze import (
    ANSWERS_PATH,
    RESULTS_DIR,
    encode,
    letter_counts,
    load_words,
    pattern_codes,
    score_guess,
)

PAIR = ("soare", "clint")
STATE_CHARS = {0: "X", 1: "Y", 2: "G"}

STRATEGY_LABELS = {
    0: "Burn word",
    1: "Split candidates",
    2: "Guess candidate",
    3: "Guess candidate",
    4: "Guess candidate",
    5: "Solved",
}


def decode_pattern(code: int) -> str:
    chars = []
    for _ in range(5):
        chars.append(STATE_CHARS[code % 3])
        code //= 3
    return "".join(chars)


def hits_for(word: str, p1: int, p2: int) -> int:
    present = set()
    for guess, pat in [(PAIR[0], p1), (PAIR[1], p2)]:
        for pos in range(5):
            if (pat // (3**pos)) % 3 > 0:
                present.add(guess[pos])
    return len(present)


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
        h = hits_for(word, p1, p2)
        buckets[h][(p1, p2)].append(word)

    rows = []
    for h in sorted(buckets):
        patterns = buckets[h]
        total = sum(len(v) for v in patterns.values())
        cand_sizes = [len(v) for v in patterns.values()]

        top_patterns = []
        for (p1, p2), words in sorted(patterns.items(), key=lambda kv: -len(kv[1]))[:3]:
            cand_codes = encode(words)
            cand_counts = letter_counts(cand_codes)
            best_word, best_entropy, best_remaining = min(
                (
                    (guess, *score_guess(ans_codes[j], cand_codes, cand_counts))
                    for j, guess in enumerate(answers)
                ),
                key=lambda row: row[2],
            )
            top_patterns.append(
                {
                    "g1": PAIR[0].upper(),
                    "g1_pattern": decode_pattern(p1),
                    "g2": PAIR[1].upper(),
                    "g2_pattern": decode_pattern(p2),
                    "candidates": len(words),
                    "guess3": best_word,
                    "expected_remaining": round(best_remaining, 2),
                }
            )

        rows.append(
            {
                "hits": h,
                "share_pct": round(100 * total / len(answers), 1),
                "answers": total,
                "patterns": len(patterns),
                "avg_candidates": round(sum(cand_sizes) / len(cand_sizes), 1),
                "max_candidates": max(cand_sizes),
                "strategy": STRATEGY_LABELS[h],
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
        "| Hits | Share | Patterns | Avg left | Max left | Strategy |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['hits']} | {row['share_pct']}% | {row['patterns']} "
            f"| {row['avg_candidates']} | {row['max_candidates']} "
            f"| {row['strategy']} |"
        )

    for row in rows:
        lines.append("")
        lines.append(f"## {row['hits']} hits — {row['strategy']}")
        lines.append("")
        lines.append(
            f"{row['share_pct']}% of games, {row['patterns']} patterns, "
            f"avg {row['avg_candidates']} candidates"
        )
        lines.append("")
        lines.append(
            "| Guess 1 | Pattern | Guess 2 | Pattern | Cands | Guess 3 | Left |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for tp in row["top_patterns"]:
            lines.append(
                f"| {tp['g1']} | {tp['g1_pattern']} | {tp['g2']} | {tp['g2_pattern']} "
                f"| {tp['candidates']} | {tp['guess3'].upper()} "
                f"| {tp['expected_remaining']} |"
            )

    (RESULTS_DIR / "hit_tree.md").write_text("\n".join(lines) + "\n")

    for row in rows:
        print(
            f"  {row['hits']} hits  {row['share_pct']:5.1f}%  "
            f"patterns {row['patterns']:3}  avg {row['avg_candidates']:4}  "
            f"max {row['max_candidates']:3}  -> {row['strategy']}"
        )


if __name__ == "__main__":
    main()
