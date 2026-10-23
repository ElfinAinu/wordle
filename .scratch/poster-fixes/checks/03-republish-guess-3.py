#!/usr/bin/env python3
"""Ticket 03 check: poster sections III and IV republished from the rule.

Recomputes the hit-count reference table (section III) and every per-pattern
row (section IV) of the shipped poster (infographic-v4.html) from
data/answers.txt with pure Python, and asserts the ticket's criteria:

  * every displayed candidate count, avg-left, max-left and candidates-left
    figure reproduces from the committed inputs;
  * every displayed word is the rule's chosen word, and its action label
    (Candidate / Split word / Burn word) is true of that word;
  * the row's action label is emitted next to the word, not hand-picked;
  * the section prose states the one-sentence rule;
  * no tier name promises an action the shown word does not perform, and the
    five-hit row carries the anagram-tie caveat.

Run: python3 .scratch/poster-fixes/checks/03-republish-guess-3.py
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANSWERS_PATH = ROOT / "data" / "answers.txt"
POSTER_PATH = ROOT / "infographic-v4.html"
HIT_TREE_JSON = ROOT / "results" / "hit_tree.json"

SOARE = "soare"
CLINT = "clint"
TOP_N = 3
ACTION_ORDER = ["Candidate", "Split word", "Burn word"]


def feedback(guess: str, answer: str) -> str:
    """Standard Wordle feedback (greens first, yellows left to right)."""
    result = ["X"] * 5
    remaining: dict[str, int] = defaultdict(int)
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = "G"
        else:
            remaining[answer[i]] += 1
    for i in range(5):
        if result[i] == "G":
            continue
        if remaining[guess[i]] > 0:
            result[i] = "Y"
            remaining[guess[i]] -= 1
    return "".join(result)


def load_answers() -> list[str]:
    return [w.strip().lower() for w in ANSWERS_PATH.read_text().split() if w.strip()]


def hit_letters(patterns: tuple[str, str]) -> set[str]:
    letters: set[str] = set()
    for guess, pattern in zip((SOARE, CLINT), patterns):
        for i, ch in enumerate(pattern):
            if ch != "X":
                letters.add(guess[i])
    return letters


def group_counts(guess: str, pool: list[str]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for answer in pool:
        counts[feedback(guess, answer)] += 1
    return counts


def sum_sq(guess: str, pool: list[str]) -> int:
    counts = group_counts(guess, pool)
    return sum(size * size for size in counts.values())


def choose_word(answers: list[str], pool: list[str]) -> tuple[str, int, bool]:
    in_pool = set(pool)
    best_key = None
    best_word = None
    best_sq = None
    for word in answers:
        sq = sum_sq(word, pool)
        key = (sq, 0 if word in in_pool else 1, word)
        if best_key is None or key < best_key:
            best_key, best_word, best_sq = key, word, sq
    assert best_word is not None and best_sq is not None
    return best_word, best_sq, best_word in in_pool


def label(word: str, in_pool: bool, letters: set[str]) -> str:
    if in_pool:
        return "Candidate"
    return "Split word" if set(word) & letters else "Burn word"


def build_buckets(answers: list[str]) -> dict[int, dict[tuple[str, str], list[str]]]:
    buckets: dict[int, dict[tuple[str, str], list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for answer in answers:
        key = (feedback(SOARE, answer), feedback(CLINT, answer))
        buckets[len(hit_letters(key))][key].append(answer)
    return buckets


def top_patterns(
    patterns: dict[tuple[str, str], list[str]]
) -> list[tuple[tuple[str, str], list[str]]]:
    # Mirror hit_tree.py: size desc, then the decoded pattern strings.
    return sorted(
        patterns.items(),
        key=lambda kv: (-len(kv[1]), kv[0][0], kv[0][1]),
    )[:TOP_N]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    end = html.index("</section>", start)
    return html[start : start + (end - start)]


def parse_reference(html: str) -> list[list[str]]:
    section = get_section(html, "reference")
    table = re.search(r"<table[^>]*>.*?</table>", section, re.S)
    assert table, "section III has no table"
    tbody = re.search(r"<tbody>(.*?)</tbody>", table.group(0), re.S)
    assert tbody, "section III table has no tbody"
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.S):
        rows.append(
            [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        )
    return rows


def parse_cards(html: str) -> list[dict]:
    section = get_section(html, "patterns")
    cards = []
    for chunk in section.split('<div class="pat-card">')[1:]:
        heading = re.search(r"<h3>(.*?)</h3>", chunk, re.S)
        sub = re.search(r'<p class="pat-sub">(.*?)</p>', chunk, re.S)
        tbody = re.search(r"<tbody>(.*?)</tbody>", chunk, re.S)
        note = re.search(r'<p class="chart-note"[^>]*>(.*?)</p>', chunk, re.S)
        rows = []
        if tbody:
            for tr in re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.S):
                rows.append(
                    [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
                )
        cards.append(
            {
                "heading": clean(heading.group(1)) if heading else "",
                "sub": clean(sub.group(1)) if sub else "",
                "rows": rows,
                "note": clean(note.group(1)) if note else "",
            }
        )
    return cards


def as_int(text: str) -> int:
    return int(re.sub(r"[^0-9-]", "", text))


def as_float(text: str) -> float:
    return float(re.sub(r"[^0-9.]", "", text))


def main() -> int:
    failures: list[str] = []
    answers = load_answers()
    buckets = build_buckets(answers)
    rule = json.loads(HIT_TREE_JSON.read_text())[0]["rule"]
    html = POSTER_PATH.read_text()
    reference_section = get_section(html, "reference")
    patterns_section = get_section(html, "patterns")

    ref_rows = parse_reference(html)
    if len(ref_rows) != len(buckets):
        failures.append(
            f"section III has {len(ref_rows)} rows, expected {len(buckets)}"
        )
    for row, hits in zip(ref_rows, sorted(buckets)):
        if len(row) != 6:
            failures.append(f"section III row {hits} has {len(row)} cells, expected 6")
            continue
        pools = buckets[hits]
        sizes = [len(v) for v in pools.values()]
        want_share = round(100 * sum(sizes) / len(answers), 1)
        want_patterns = len(pools)
        want_avg = round(sum(sizes) / len(sizes), 1)
        want_max = max(sizes)
        want_actions = [
            action
            for action in ACTION_ORDER
            if action
            in [
                label(
                    choose_word(answers, pool)[0],
                    choose_word(answers, pool)[2],
                    hit_letters(pair),
                )
                for pair, pool in top_patterns(pools)
            ]
        ]
        got_hits, got_share, got_patterns, got_avg, got_max, got_actions = row
        if as_int(got_hits) != hits:
            failures.append(f"section III row {hits}: hit label mismatch")
        if as_float(got_share) != want_share:
            failures.append(
                f"section III row {hits}: share {got_share} != {want_share}"
            )
        if as_int(got_patterns) != want_patterns:
            failures.append(
                f"section III row {hits}: patterns {got_patterns} != {want_patterns}"
            )
        if as_float(got_avg) != want_avg:
            failures.append(f"section III row {hits}: avg {got_avg} != {want_avg}")
        if as_int(got_max) != want_max:
            failures.append(f"section III row {hits}: max {got_max} != {want_max}")
        shown_actions = got_actions.split("·")[0].strip()
        got_set = {a.strip() for a in shown_actions.split(",") if a.strip()}
        if got_set != set(want_actions):
            failures.append(
                f"section III row {hits}: actions {got_set} != {set(want_actions)}"
            )
        if hits == 5:
            if "Solved" in got_actions:
                failures.append("section III still labels the five-hit row Solved")
            if "anagram" not in got_actions.lower() and "tie" not in got_actions.lower():
                failures.append(
                    "section III five-hit row has no anagram-tie caveat"
                )
        for action in showed_actions_of(got_actions):
            if action not in ACTION_ORDER:
                failures.append(
                    f"section III row {hits}: unknown action label {action!r}"
                )

    if "Solved" in reference_section:
        failures.append("section III still contains the word 'Solved'")

    section_text = clean(reference_section + " " + patterns_section)
    if clean(rule) not in section_text:
        failures.append("sections III/IV do not state the one-sentence rule")

    cards = parse_cards(html)
    if [as_int(c["heading"].split()[0]) for c in cards] != sorted(buckets):
        failures.append("section IV cards are not one per hit count in order")

    for card, hits in zip(cards, sorted(buckets)):
        pools = buckets[hits]
        expected_pairs = top_patterns(pools)
        if re.search(
            r"\b(Candidate|Split(?: word)?|Burn(?: word)?)\b", card["heading"]
        ):
            failures.append(
                f"section IV {hits} hits: title still names an action: "
                f"{card['heading']!r}"
            )
        if "largest" not in card["sub"].lower():
            failures.append(
                f"section IV {hits} hits: subtitle does not say the rows are the "
                f"band's largest pools: {card['sub']!r}"
            )
        pool_claim = re.search(rf"(\d+)\s+of\s+{len(pools)}\b", card["sub"])
        if not pool_claim or int(pool_claim.group(1)) != len(card["rows"]):
            failures.append(
                f"section IV {hits} hits: subtitle {card['sub']!r} does not state "
                f"{len(card['rows'])} of {len(pools)} largest pools"
            )
        if len(card["rows"]) != len(expected_pairs):
            failures.append(
                f"section IV {hits} hits: {len(card['rows'])} rows, "
                f"expected {len(expected_pairs)}"
            )
            continue
        for row, (pair, pool) in zip(card["rows"], expected_pairs):
            if len(row) != 6:
                failures.append(
                    f"section IV {hits} hits {pair}: {len(row)} cells, expected 6"
                )
                continue
            got_g1, got_g2, got_count, got_action, got_word, got_left = row
            want_word, want_sq, want_in_pool = choose_word(answers, pool)
            want_action = label(want_word, want_in_pool, hit_letters(pair))
            if (got_g1, got_g2) != pair:
                failures.append(
                    f"section IV {hits} hits: displayed {got_g1}/{got_g2} != {pair}"
                )
            if as_int(got_count) != len(pool):
                failures.append(
                    f"section IV {pair}: count {got_count} != {len(pool)}"
                )
            if got_word.lower() != want_word:
                failures.append(
                    f"section IV {pair}: word {got_word} != rule word {want_word}"
                )
            if got_action != want_action:
                failures.append(
                    f"section IV {pair}: action {got_action!r} != {want_action!r}"
                )
            want_left = round(want_sq / len(pool), 2)
            if as_float(got_left) != want_left:
                failures.append(
                    f"section IV {pair}: left {got_left} != {want_left}"
                )
            if want_action == "Candidate":
                if want_word not in set(pool):
                    failures.append(f"section IV {pair}: candidate not in pool")
            elif want_word in set(pool):
                failures.append(
                    f"section IV {pair}: {want_action} word {want_word} is in pool"
                )
        if hits == 5:
            if not re.search(r"anagram|tie", card["note"], re.IGNORECASE):
                failures.append("section IV five-hit card has no anagram-tie caveat")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    print(f"  answers={len(answers)}  buckets={sorted(buckets)}")
    print("  section III counts, avgs, maxes and action sets reproduced")
    print("  section IV words, counts, lefts and action labels reproduced")
    print("  five-hit caveat and one-sentence rule present")
    return 0


def showed_actions_of(cell: str) -> list[str]:
    return [a.strip() for a in cell.split("·")[0].split(",") if a.strip()]


if __name__ == "__main__":
    sys.exit(main())
