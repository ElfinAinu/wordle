#!/usr/bin/env python3
"""Acceptance check for ticket 02: section IX, "Full vowel coverage".

Re-derives the six single-vowel branches from data/answers.txt and fails when
any figure on the poster drifts, then checks the conditions the section depends
on:

  * every branch's answer count, share of games, vowel-repeat share, next guess
    and expected-candidates-left match the chart, and each bar's height is the
    repeat share scaled to the tallest;
  * the rule the section teaches is re-derived, not grepped: for E and O the
    best next guess must repeat a letter, and for A, I, U and Y it must not;
  * the section's claim that no answer has zero of A E I O U Y holds;
  * the denominators it names are the branch sizes;
  * the cost figures match results/full_coverage.json;
  * the section stays conditional - section I still states two openers and ten
    letters tested, and section IX cross-references III and IV.

Run: python3 .scratch/full-coverage/checks/02-section-full-coverage.py

For a negative test, point POSTER_PATH at a mutated copy:

  POSTER_PATH=/tmp/mutated.html python3 .scratch/full-coverage/checks/02-section-full-coverage.py
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from analyze import (
    ANSWERS_PATH,
    encode,
    letter_counts,
    load_words,
    score_guess,
)

POSTER_PATH = Path(os.environ.get("POSTER_PATH", ROOT / "infographic-v4.html"))
RESULTS_PATH = ROOT / "results" / "full_coverage.json"

WORD_LENGTH = 5
FULL_VOWELS = set("aeiouy")

# Branches whose best next guess must repeat a letter, and branches whose best
# guess must carry five distinct letters. This is the rule the section teaches;
# the check re-derives it rather than trusting the prose.
WANT_DOUBLE = {"e", "o"}
WANT_DISTINCT = {"a", "i", "u", "y"}

CARD_RE = re.compile(
    r'<div class="dist-col">'
    r'<span class="dist-bar"><i(?: class="opt")? style="height:(?P<height>\d+)%"></i></span>'
    r'<span class="dist-val">(?P<repeat>[\d.]+)%</span>'
    r'<span class="dist-lab">(?P<vowel>[A-Z])</span>'
    r'<span class="vowel-share">(?P<games>[\d.]+)% of games</span>'
    r'<span class="vowel-pick">(?P<pick>[A-Z]+)</span>'
    r'<span class="vowel-left">(?P<left>[\d.]+) left</span>'
    r"</div>"
)


def branch_for(words: list[str], vowel: str) -> list[str]:
    return [w for w in words if {c for c in w if c in FULL_VOWELS} == {vowel}]


def best_pick(pool: list[str], guess_words: list[str], guess_codes):
    counts = letter_counts(encode(pool))
    pool_codes = encode(pool)
    return min(
        (
            (guess, *score_guess(guess_codes[index], pool_codes, counts))
            for index, guess in enumerate(guess_words)
        ),
        key=lambda row: row[2],
    )


def share(part: int, whole: int) -> float:
    return round(100 * part / whole, 1)


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    return html[start : html.index("</section>", start)]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    failures: list[str] = []
    words = load_words(ANSWERS_PATH)
    total = len(words)
    guess_codes = encode(words)

    # --- re-derive the branches ---------------------------------------------
    branches = {}
    for vowel in sorted(FULL_VOWELS):
        pool = branch_for(words, vowel)
        pick, _entropy, left = best_pick(pool, words, guess_codes)
        branches[vowel] = {
            "answers": len(pool),
            "share": share(len(pool), total),
            "repeat": share(sum(1 for w in pool if Counter(w)[vowel] > 1), len(pool)),
            "pick": pick.upper(),
            "left": round(left, 2),
        }

    zero_vowel = sum(1 for w in words if not ({c for c in w} & FULL_VOWELS))
    if zero_vowel != 0:
        failures.append(
            f"{zero_vowel} answers have no A E I O U Y; the section claims none do"
        )

    # The rule: E and O want a double, A/I/U/Y want five distinct letters.
    for vowel, want in [(v, True) for v in WANT_DOUBLE] + [
        (v, False) for v in WANT_DISTINCT
    ]:
        pick = branches[vowel]["pick"]
        has_repeat = len(set(pick.lower())) < WORD_LENGTH
        if has_repeat != want:
            failures.append(
                f"re-derived pick for {vowel.upper()} is {pick} "
                f"({'repeat' if has_repeat else 'distinct'}); the section teaches "
                f"{'repeat' if want else 'distinct'}"
            )

    tallest = max(b["repeat"] for b in branches.values())

    # --- the poster ----------------------------------------------------------
    html = POSTER_PATH.read_text()
    if 'id="vowels"' not in html:
        print("FAIL")
        print('  - poster has no section id="vowels"')
        return 1
    section = get_section(html, "vowels")
    text = clean(section)
    method = get_section(html, "method")
    method_text = clean(method)

    cards = {}
    for match in CARD_RE.finditer(section):
        cards[match.group("vowel")] = match
    if len(cards) != len(FULL_VOWELS):
        failures.append(
            f"chart has {len(cards)} vowel cards, expected {len(FULL_VOWELS)}"
        )

    for vowel, expected in branches.items():
        card = cards.get(vowel.upper())
        if card is None:
            failures.append(f"chart has no card for {vowel.upper()}")
            continue
        if abs(float(card.group("games")) - expected["share"]) > 0.005:
            failures.append(
                f"{vowel.upper()} card states {card.group('games')}% of games, "
                f"expected {expected['share']}%"
            )
        if abs(float(card.group("repeat")) - expected["repeat"]) > 0.005:
            failures.append(
                f"{vowel.upper()} card states a {card.group('repeat')}% repeat "
                f"share, expected {expected['repeat']}%"
            )
        if card.group("pick") != expected["pick"]:
            failures.append(
                f"{vowel.upper()} card recommends {card.group('pick')}, "
                f"expected {expected['pick']}"
            )
        if abs(float(card.group("left")) - expected["left"]) > 0.005:
            failures.append(
                f"{vowel.upper()} card states {card.group('left')} left, "
                f"expected {expected['left']}"
            )
        expected_height = round(100 * expected["repeat"] / tallest)
        if abs(int(card.group("height")) - expected_height) > 1:
            failures.append(
                f"{vowel.upper()} bar is {card.group('height')}% tall, "
                f"expected about {expected_height}% "
                f"(repeat share {expected['repeat']}% of {tallest}%)"
            )
        if str(expected["answers"]) not in text:
            failures.append(
                f"section does not name the {vowel.upper()} branch size "
                f"({expected['answers']} answers)"
            )

    # Denominators: branch sizes, explicitly not section VIII's figures.
    if "branch sizes" not in text.lower():
        failures.append("section does not name its denominators as branch sizes")
    if "repeated-letter-instance" not in text.lower():
        failures.append(
            "section does not distinguish its denominator from section VIII's"
        )

    # --- the section stays conditional --------------------------------------
    if "Two openers · one decision" not in method_text:
        failures.append("section I no longer states the two-opener standard")
    if "10 letters tested" not in method_text:
        failures.append("section I no longer states ten letters tested")
    if "Sections III and IV" not in text:
        failures.append("section IX does not cross-reference sections III and IV")
    if "spend guess 3 on a coverage word" not in text:
        failures.append("section IX does not frame itself as the conditional move")

    # --- the cost figures match the measurement -----------------------------
    if not RESULTS_PATH.exists():
        failures.append(
            f"{RESULTS_PATH.relative_to(ROOT)} is missing; run full_coverage.py"
        )
    else:
        cost = json.loads(RESULTS_PATH.read_text()).get("cost", {})
        if cost:
            two = round(cost["two_openers"]["average_guesses"], 2)
            three = round(cost["three_openers"]["average_guesses"], 2)
            for value in (f"{two:.2f}", f"{three:.2f}"):
                if value not in text:
                    failures.append(f"section does not state the coverage cost {value}")
            if f"{round(cost['extra_guesses'], 2):.2f}" not in text:
                failures.append("section does not state the extra guesses per game")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    for vowel, expected in branches.items():
        print(
            f"  {vowel.upper()}: {expected['answers']} answers ({expected['share']}%), "
            f"repeat {expected['repeat']}% -> {expected['pick']} "
            f"{expected['left']} left"
        )
    print("  rule re-derived: E and O want a double; A, I, U and Y want five distinct")
    print("  no answer has zero of A E I O U Y; section I unchanged, two openers")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"FAIL\n  - {exc}")
        sys.exit(1)
