#!/usr/bin/env python3
"""Acceptance check for ticket 03: the vowel-count table in section IX.

Re-derives the vowel-count distribution for both pools and both counting
conventions from data/answers.txt and data/allowed.txt, and fails when any cell
on the poster drifts.

  * every cell of Fig. 10 matches the re-derived share, under A E I O U and
    under A E I O U Y, for the answers pool and for all valid words;
  * the 3+ row really is the roll-up of the rows above it, under both
    conventions, rather than an independent figure that could disagree;
  * the five-vowel caveat the table states is true of the valid pool;
  * the table names its denominators, and they are the pool sizes rather than
    section IX's branch sizes or section VIII's repeat counts;
  * the Y figures live in the table only - the separate "Counting Y as well"
    card is gone, so no figure is stated twice.

Run: python3 .scratch/full-coverage/checks/03-vowel-count-table.py

For a negative test, point POSTER_PATH at a mutated copy:

  POSTER_PATH=/tmp/mutated.html python3 .scratch/full-coverage/checks/03-vowel-count-table.py
"""

import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANSWERS_PATH = ROOT / "data" / "answers.txt"
ALLOWED_PATH = ROOT / "data" / "allowed.txt"
POSTER_PATH = Path(os.environ.get("POSTER_PATH", ROOT / "infographic-v4.html"))

PLAIN = "aeiou"
WITH_Y = "aeiouy"
VOWEL_SETS = {PLAIN: set(PLAIN), WITH_Y: set(WITH_Y)}
MAX_VOWELS = 5

# <tr><td class="big">LABEL</td><td class="num-col">P% <i>(Y%)</i></td> ... </tr>
ROW_RE = re.compile(
    r'<tr><td class="big">(?P<label>[^<]+)</td>'
    r'<td class="num-col">(?P<answers>[\d.]+)% <i>\((?P<answers_y>[\d.]+)%\)</i></td>'
    r'<td class="num-col">(?P<valid>[\d.]+)% <i>\((?P<valid_y>[\d.]+)%\)</i></td></tr>'
)


def load_words(path: Path) -> list[str]:
    return [
        line.strip().lower() for line in path.read_text().splitlines() if line.strip()
    ]


def share(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def distribution(words: list[str], vowels: set[str]) -> dict:
    total = len(words)
    tally = Counter(sum(1 for ch in word if ch in vowels) for word in words)
    more_than_two = sum(n for count, n in tally.items() if count > 2)
    return {
        "total": total,
        "shares": {
            count: share(tally.get(count, 0), total) for count in range(MAX_VOWELS + 1)
        },
        "counts": {count: tally.get(count, 0) for count in range(MAX_VOWELS + 1)},
        "more_than_two": more_than_two,
        "more_than_two_pct": share(more_than_two, total),
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
    answers = load_words(ANSWERS_PATH)
    allowed = load_words(ALLOWED_PATH)
    all_valid = sorted(set(answers) | set(allowed))

    pools = {"answers": answers, "valid": all_valid}
    derived = {
        (label, name): distribution(words, VOWEL_SETS[name])
        for label, words in pools.items()
        for name in (PLAIN, WITH_Y)
    }

    if derived[("valid", PLAIN)]["total"] != 14855:
        failures.append(
            f"all-valid pool is {derived[('valid', PLAIN)]['total']}, expected 14855"
        )
    if len(allowed) != 12546:
        failures.append(f"allowed pool is {len(allowed)}, expected 12546")

    # The 3+ row must be the roll-up of the rows above it, under both conventions.
    for label in pools:
        for name in (PLAIN, WITH_Y):
            stats = derived[(label, name)]
            rolled = sum(stats["counts"][k] for k in range(3, MAX_VOWELS + 1))
            if rolled != stats["more_than_two"]:
                failures.append(
                    f"{label}/{name}: 3+ roll-up is {rolled} but more-than-two "
                    f"is {stats['more_than_two']}"
                )

    html = POSTER_PATH.read_text()
    if 'id="vowels"' not in html:
        print("FAIL")
        print('  - poster has no section id="vowels"')
        return 1
    section = get_section(html, "vowels")
    text = clean(section)

    # --- the table -----------------------------------------------------------
    rows = {}
    for match in ROW_RE.finditer(section):
        rows[match.group("label").strip()] = {
            "answers": float(match.group("answers")),
            "answers_y": float(match.group("answers_y")),
            "valid": float(match.group("valid")),
            "valid_y": float(match.group("valid_y")),
        }

    for count in range(MAX_VOWELS + 1):
        label = str(count)
        if label not in rows:
            if any(
                derived[(pool, name)]["shares"][count]
                for pool in pools
                for name in (PLAIN, WITH_Y)
            ):
                failures.append(f"table has no row for {count} vowels")
            continue
        got = rows[label]
        for pool, suffix in (("answers", ""), ("valid", "")):
            for name, key in ((PLAIN, suffix), (WITH_Y, f"{suffix}_y")):
                want = derived[(pool, name)]["shares"][count]
                if abs(got[f"{pool}{key}"] - want) > 0.05:
                    failures.append(
                        f"row {count}: {pool} cell ({name}) is "
                        f"{got[f'{pool}{key}']}%, expected {want}%"
                    )

    if "3+" not in rows:
        failures.append("table has no 3+ roll-up row")
    else:
        got = rows["3+"]
        for pool in pools:
            for name, key in ((PLAIN, ""), (WITH_Y, "_y")):
                want = derived[(pool, name)]["more_than_two_pct"]
                if abs(got[f"{pool}{key}"] - want) > 0.05:
                    failures.append(
                        f"3+ {pool} cell ({name}) is {got[f'{pool}{key}']}%, "
                        f"expected {want}%"
                    )

    # The five-vowel caveat must be true of the valid pool.
    five = derived[("valid", WITH_Y)]["counts"][5]
    if five != 3:
        failures.append(f"valid pool has {five} five-vowel words, expected 3")
    if "three valid words" not in text:
        failures.append("table does not state the five-vowel caveat")

    # --- the Y figures live in the table only --------------------------------
    if "Counting Y as well" in text:
        failures.append("the separate Counting-Y card is back; Y is stated twice")
    if "in parentheses" not in text:
        failures.append("table does not explain the parenthetical figures")

    # --- denominators --------------------------------------------------------
    for figure in ("2,309", "14,855", "12,546"):
        if figure not in text:
            failures.append(f"table does not name the denominator {figure}")
    if "each pool's own size" not in text:
        failures.append("table does not say its shares use each pool's own size")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    for label in pools:
        for name in (PLAIN, WITH_Y):
            stats = derived[(label, name)]
            cells = ", ".join(
                f"{count}:{stats['shares'][count]}%" for count in range(MAX_VOWELS + 1)
            )
            print(f"  {label:8} {name:7} {cells}")
            print(
                f"  {'':8} {'':7} 3 or more: {stats['more_than_two']} "
                f"({stats['more_than_two_pct']}%)"
            )
    print(f"  valid words reaching five vowels once Y counts: {five}")
    print("  Y figures appear in the table only, no duplicate card")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"FAIL\n  - {exc}")
        sys.exit(1)
