#!/usr/bin/env python3
"""Acceptance check for ticket 02: poster section VIII, "Where repeats sit".

Re-derives every figure the section prints straight from data/answers.txt and
fails when any drifts:

  * the section exists as VIII, appended after "Shape & mistakes" (VII), with
    no existing numeral renumbered;
  * the grid is a 5x5 upper triangle, one cell per slot pair, shaded by that
    pair's share of repeat pairs, with the raw count on hover and touching
    pairs marked distinctly from separated ones;
  * the caption carries the touching/separated split (43% / 57%), the class
    skew (touching consonant-heavy, separated vowel-heavy) and the visibility
    split (81% / 19%), and states both denominators.

Run: python3 .scratch/repeats-section/checks/02-section-where-repeats-occur.py

For a negative test, point POSTER_PATH at a mutated copy:

  POSTER_PATH=/tmp/mutated.html python3 .scratch/repeats-section/checks/02-section-where-repeats-occur.py
"""

import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANSWERS_PATH = ROOT / "data" / "answers.txt"
POSTER_PATH = Path(os.environ.get("POSTER_PATH", ROOT / "infographic-v4.html"))

WORD_LENGTH = 5
VOWELS = set("aeiou")
OPENING_LETTERS = set("soareclint")

ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]

# <span class="hm-cell[--mod]" style="--ink:NN%" title="A-B slots: C of D repeat
# pairs (S.S%); touching|separated">S.S</span>
CELL_RE = re.compile(
    r'<span class="hm-cell(?P<mods>[^"]*)"[^>]*style="--ink:(?P<ink>\d+)%" '
    r'title="(?P<a>\d)-(?P<b>\d) slots: (?P<count>\d+) of (?P<denom>\d+) repeat pairs '
    r'\((?P<share>[\d.]+)%\); (?P<kind>touching|separated)">(?P<text>[^<]*)</span>'
)


def load_answers() -> list[str]:
    return [
        line.strip().lower()
        for line in ANSWERS_PATH.read_text().splitlines()
        if line.strip()
    ]


def letter_class(letter: str) -> str:
    if letter in VOWELS:
        return "vowel"
    return "y" if letter == "y" else "consonant"


def share(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def derive(words: list[str]) -> dict:
    pair_counts: Counter[tuple[int, int]] = Counter()
    touching_class: Counter[str] = Counter()
    separated_class: Counter[str] = Counter()
    repeat_words = 0
    tested = 0
    untested = 0

    for word in words:
        if len(set(word)) < WORD_LENGTH:
            repeat_words += 1
        positions: dict[str, list[int]] = {}
        for index, letter in enumerate(word):
            positions.setdefault(letter, []).append(index + 1)
        for letter, copies in Counter(word).items():
            if copies < 2:
                continue
            slots = positions[letter]
            touching = any(slots[i + 1] - slots[i] == 1 for i in range(len(slots) - 1))
            for a in range(len(slots)):
                for b in range(a + 1, len(slots)):
                    pair_counts[(slots[a], slots[b])] += 1
            (touching_class if touching else separated_class)[letter_class(letter)] += 1
            if letter in OPENING_LETTERS:
                tested += 1
            else:
                untested += 1

    pairs = sum(pair_counts.values())
    instances = sum(touching_class.values()) + sum(separated_class.values())
    touching = sum(touching_class.values())
    separated = sum(separated_class.values())
    return {
        "words": len(words),
        "pair_counts": pair_counts,
        "pairs": pairs,
        "instances": instances,
        "repeat_words": repeat_words,
        "touching": touching,
        "separated": separated,
        "touching_consonant": touching_class["consonant"],
        "separated_vowel": separated_class["vowel"],
        "tested": tested,
        "untested": untested,
        "shares": {pair: share(count, pairs) for pair, count in pair_counts.items()},
    }


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    return html[start : html.index("</section>", start)]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    failures: list[str] = []
    answers = load_answers()
    stats = derive(answers)
    html = POSTER_PATH.read_text()

    # --- section furniture: VIII appended, nothing renumbered ---------------
    romans = re.findall(r'<span class="roman">([IVX]+)</span>', html)
    if romans != ROMANS:
        failures.append(f"section numerals are {romans}, expected {ROMANS}")
    if 'id="repeats"' not in html:
        print("FAIL")
        print('  - poster has no section with id="repeats"')
        return 1

    shape = get_section(html, "shape")
    if (
        'class="roman">VII</span><h2 class="sec-title">Shape &amp; mistakes</h2>'
        not in shape
    ):
        failures.append("section VII is no longer the shape-and-mistakes section")
    repeats = get_section(html, "repeats")
    if 'class="roman">VIII</span>' not in repeats:
        failures.append("the repeats section is not numbered VIII")
    if html.index('id="repeats"') < html.index('id="shape"'):
        failures.append("the repeats section is not appended after section VII")

    # --- grid: 5x5 upper triangle, one cell per slot pair -------------------
    cells = []
    for match in CELL_RE.finditer(repeats):
        a, b = int(match.group("a")), int(match.group("b"))
        mods, ink, count = (
            match.group("mods"),
            int(match.group("ink")),
            int(match.group("count")),
        )
        denom = int(match.group("denom"))
        cell_share = float(match.group("share"))
        kind, text = match.group("kind"), match.group("text")
        touching = b - a == 1
        if not 1 <= a < b <= 5:
            failures.append(f"cell {a}-{b} is not in the upper triangle")
            continue
        if denom != stats["pairs"]:
            failures.append(
                f"cell {a}-{b} denominator is {denom}, expected {stats['pairs']}"
            )
        expected = stats["pair_counts"].get((a, b), 0)
        if count != expected:
            failures.append(f"cell {a}-{b} count is {count}, expected {expected}")
        expected_share = stats["shares"].get((a, b))
        if cell_share != expected_share:
            failures.append(
                f"cell {a}-{b} share is {cell_share}%, expected {expected_share}%"
            )
        if text != f"{expected_share:.1f}":
            failures.append(
                f"cell {a}-{b} prints {text!r}, expected {expected_share:.1f}"
            )
        if kind != ("touching" if touching else "separated"):
            failures.append(f"cell {a}-{b} is labelled {kind!r}, expected the opposite")
        if ("hm-cell--touch" in mods) != touching:
            failures.append(f"cell {a}-{b} touching style does not match its slots")
        cells.append((a, b, cell_share, ink))

    if len(cells) != 10:
        failures.append(
            f"grid has {len(cells)} filled cells, expected 10 (5x5 upper triangle)"
        )
    if {(a, b) for a, b, _, _ in cells} != set(stats["pair_counts"]):
        failures.append("grid cells do not match the set of slot pairs in the answers")
    if repeats.count("hm-cell--void") != 15:
        failures.append(
            f"grid has {repeats.count('hm-cell--void')} void cells, expected 15 "
            "(the lower triangle plus diagonal)"
        )

    # Shading must follow the share: a bigger share can never be paler.
    by_share = sorted(cells, key=lambda cell: cell[2])
    for (_, _, share_a, ink_a), (_, _, share_b, ink_b) in zip(by_share, by_share[1:]):
        if share_b > share_a and ink_b < ink_a:
            failures.append(
                f"shading is inverted: share {share_a}% has ink {ink_a}% but "
                f"share {share_b}% has ink {ink_b}%"
            )

    # Header labels 1..5 and every pair's raw count on hover (title attribute).
    header = re.search(r'<div class="hm-head">(.*?)</div>', repeats, re.DOTALL)
    if not header or re.findall(r"<span>(\d)</span>", header.group(1)) != [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]:
        failures.append("grid header does not label columns 1-5")
    if repeats.count("slots:") != 10:
        failures.append("not every grid cell carries its raw count in a title")

    # --- caption figures ----------------------------------------------------
    touch_pct = share(stats["touching"], stats["instances"])
    sep_pct = share(stats["separated"], stats["instances"])
    touch_consonant_pct = share(stats["touching_consonant"], stats["touching"])
    sep_vowel_pct = share(stats["separated_vowel"], stats["separated"])
    tested_pct = share(stats["tested"], stats["instances"])
    untested_pct = share(stats["untested"], stats["instances"])
    repeat_word_pct = share(stats["repeat_words"], stats["words"])

    # Every labelled row of the split panel states its own derived figure.
    shape_rows = {
        clean(label): clean(value)
        for label, value in re.findall(
            r'<div class="shape-row"><span>(.*?)</span><b>(.*?)</b></div>',
            repeats,
            re.DOTALL,
        )
    }
    expected_rows = {
        "repeats that touch": f"{touch_pct:.0f}%",
        "repeats that are separated": f"{sep_pct:.0f}%",
        "touching repeats that are consonants": f"{touch_consonant_pct:.0f}%",
        "separated repeats that are vowels": f"{sep_vowel_pct:.0f}%",
        "opening tests the repeated letter": f"{tested_pct:.0f}%",
        "opening never tests it": f"{untested_pct:.0f}%",
    }
    for label, token in expected_rows.items():
        if shape_rows.get(label) != token:
            failures.append(
                f"row {label!r} states {shape_rows.get(label)!r}, expected {token!r}"
            )

    note = re.search(r'<p class="note-line">(.*?)</p>', repeats, re.DOTALL)
    note_text = clean(note.group(1)) if note else ""
    if not note_text:
        failures.append("section has no caption note (.note-line)")
    for label, token in expected_rows.items():
        if token not in note_text:
            failures.append(f"caption does not restate the {label} ({token})")
    note_counts = {
        "repeated-letter instances": stats["instances"],
        "touching instances": stats["touching"],
        "separated instances": stats["separated"],
        "touching consonants": stats["touching_consonant"],
        "separated vowels": stats["separated_vowel"],
        "tested instances": stats["tested"],
        "untested instances": stats["untested"],
    }
    for label, number in note_counts.items():
        if str(number) not in note_text:
            failures.append(f"caption does not state the {label} ({number})")
    if f"{stats['instances']} repeated-letter instances" not in note_text:
        failures.append("caption does not name the repeated-letter-instance denominator")

    chart = re.search(r'<p class="chart-note">(.*?)</p>', repeats, re.DOTALL)
    chart_text = clean(chart.group(1)) if chart else ""
    if not chart_text:
        failures.append("grid panel has no caption note (.chart-note)")
    if f"{stats['pairs']} repeat pairs" not in chart_text:
        failures.append("grid caption does not name the repeat-pair denominator")
    chart_counts = {
        "repeat words": f"{stats['repeat_words']}",
        "answers": f"{stats['words']:,}",
        "repeat-word share": f"{repeat_word_pct:.1f}%",
    }
    for label, token in chart_counts.items():
        if token not in chart_text:
            failures.append(f"grid caption does not state the {label} ({token})")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    print("  sections I-VIII intact; repeats is VIII")
    print(
        f"  grid: 10 cells / {stats['pairs']} repeat pairs, largest 3-4 at "
        f"{stats['shares'][(3, 4)]}%"
    )
    print(
        f"  split: {stats['touching']} touching ({touch_pct}%) / "
        f"{stats['separated']} separated ({sep_pct}%) of {stats['instances']} instances"
    )
    print(
        f"  visibility: {stats['tested']} tested ({tested_pct}%) / "
        f"{stats['untested']} untested ({untested_pct}%)"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"FAIL\n  - {exc}")
        sys.exit(1)
