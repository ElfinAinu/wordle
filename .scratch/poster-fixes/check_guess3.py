# /// script
# requires-python = ">=3.11"
# ///
"""Independent acceptance check for results/hit_tree.{json,md}.

Recomputes the guess-3 table from data/answers.txt with a from-scratch
Wordle feedback function (no imports from the analysis modules) and asserts
every acceptance criterion in .scratch/poster-fixes/issues/02-guess-3-rule.md:

  * every recommended word's action label is true of that word;
  * a candidate-labelled word is no worse than the best in-pool word;
  * the displayed rows are the largest candidate pools per hit count;
  * the analysis emits the action label next to each word;
  * the one-sentence rule is present.

Run:  python .scratch/poster-fixes/check_guess3.py
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANSWERS_PATH = ROOT / "data" / "answers.txt"
RESULTS_DIR = ROOT / "results"
PAIR = ("soare", "clint")
TOP_N = 3


def load_words(path: Path) -> list[str]:
    return [line.strip().lower() for line in path.read_text().splitlines() if line.strip()]


def feedback(guess: str, answer: str) -> str:
    """Standard Wordle feedback (greens first, then yellows left to right)."""
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


def hit_letters(pattern_pair: tuple[str, str]) -> set[str]:
    letters = set()
    for guess, pattern in zip(PAIR, pattern_pair):
        for i, ch in enumerate(pattern):
            if ch != "X":
                letters.add(guess[i])
    return letters


def sum_sq(guess: str, pool: list[str]) -> int:
    groups: dict[str, int] = defaultdict(int)
    for answer in pool:
        groups[feedback(guess, answer)] += 1
    return sum(size * size for size in groups.values())


def choose_word(answers: list[str], pool: list[str]) -> tuple[str, int, bool]:
    """Rule: minimise expected remaining (integer sum of squares), prefer a
    remaining candidate on ties, then alphabetical."""
    in_pool = set(pool)
    best_key = None
    best_word = None
    best_sq = None
    for word in answers:
        sq = sum_sq(word, pool)
        key = (sq, 0 if word in in_pool else 1, word)
        if best_key is None or key < best_key:
            best_key, best_word, best_sq = key, word, sq
    return best_word, best_sq, best_word in in_pool


def label(word: str, in_pool: bool, hit_set: set[str]) -> str:
    if in_pool:
        return "Candidate"
    return "Split word" if set(word) & hit_set else "Burn word"


def expected_buckets(answers: list[str]) -> dict[int, dict[tuple[str, str], list[str]]]:
    buckets: dict[int, dict[tuple[str, str], list[str]]] = defaultdict(lambda: defaultdict(list))
    for answer in answers:
        pattern_pair = tuple(feedback(guess, answer) for guess in PAIR)
        buckets[len(hit_letters(pattern_pair))][pattern_pair].append(answer)
    return buckets


def check() -> None:
    answers = load_words(ANSWERS_PATH)
    buckets = expected_buckets(answers)
    rows = json.loads((RESULTS_DIR / "hit_tree.json").read_text())
    md = (RESULTS_DIR / "hit_tree.md").read_text()

    assert isinstance(rows, list), "hit_tree.json must stay a list for poster.py"

    # Acceptance: the rule is present and is one sentence.
    rule = rows[0].get("rule")
    assert rule, "hit_tree.json rows must carry the rule"
    assert all(row.get("rule") == rule for row in rows), "rule must be identical across rows"
    assert rule.count(".") == 1 and rule.endswith("."), f"rule must be one sentence: {rule!r}"
    assert rule in md, "hit_tree.md must state the rule"

    seen_hits = []
    for row in rows:
        hits = row["hits"]
        seen_hits.append(hits)
        patterns = buckets[hits]
        expected_top = sorted(patterns.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:TOP_N]

        # Acceptance: displayed rows are the largest candidate pools for the hit count.
        got_keys = [(tp["g1_pattern"], tp["g2_pattern"]) for tp in row["top_patterns"]]
        want_keys = [pp for pp, _ in expected_top]
        assert got_keys == want_keys, f"{hits} hits rows {got_keys} != largest pools {want_keys}"

        actions = []
        for tp, (pattern_pair, pool) in zip(row["top_patterns"], expected_top):
            # Acceptance: analysis emits the action label next to each word.
            assert "action" in tp, f"missing action for {pattern_pair}"
            assert tp["candidates"] == len(pool), f"candidate count drift for {pattern_pair}"
            hit_set = hit_letters(pattern_pair)
            word, sq, in_pool = choose_word(answers, pool)
            assert tp["guess3"] == word, f"{pattern_pair}: {tp['guess3']} != rule word {word}"
            assert tp["action"] == label(word, in_pool, hit_set), f"{pattern_pair}: wrong action label"
            assert tp["in_pool"] == in_pool, f"{pattern_pair}: wrong in_pool flag"
            assert round(sq / len(pool), 2) == tp["expected_remaining"], (
                f"{pattern_pair}: expected remaining drift"
            )

            # Acceptance: candidate in pool, burn/split not in pool.
            best_in_word, best_in_sq = min(
                ((w, sum_sq(w, pool)) for w in pool), key=lambda item: (item[1], item[0])
            )
            assert tp["best_candidate"] == best_in_word, f"{pattern_pair}: best_candidate drift"
            assert round(best_in_sq / len(pool), 2) == tp["best_candidate_remaining"], (
                f"{pattern_pair}: best_candidate_remaining drift"
            )
            if tp["action"] == "Candidate":
                assert word in set(pool), f"{pattern_pair}: candidate {word} not in pool"
                assert sq <= best_in_sq, (
                    f"{pattern_pair}: candidate {word} worse ({sq}) than best in-pool ({best_in_sq})"
                )
            else:
                assert word not in set(pool), f"{pattern_pair}: {tp['action']} {word} is in pool"
                assert sq <= best_in_sq, (
                    f"{pattern_pair}: {tp['action']} {word} ({sq}) worse than best in-pool ({best_in_sq})"
                )

            actions.append(tp["action"])
        assert row["actions"] == sorted(set(actions), key=lambda a: ["Candidate", "Split word", "Burn word"].index(a)), (
            f"{hits} hits: action summary drift"
        )

    assert seen_hits == sorted(buckets), "hit-count buckets must all be present"

    # Regression: the historical bug row (2 hits, XXXYY XXXXX) must now be a
    # candidate recommendation, and no recommendation may be worse than the
    # best in-pool word when it is labelled a candidate.
    row2 = next(r for r in rows if r["hits"] == 2)
    bug_row = next(
        tp for tp in row2["top_patterns"] if (tp["g1_pattern"], tp["g2_pattern"]) == ("XXXYY", "XXXXX")
    )
    assert bug_row["action"] == "Candidate", f"regression: {bug_row}"
    assert bug_row["guess3"] in set(buckets[2][("XXXYY", "XXXXX")]), "regression: word not in pool"

    print("check_guess3: all acceptance criteria pass")


if __name__ == "__main__":
    try:
        check()
    except AssertionError as exc:
        print(f"check_guess3: FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
