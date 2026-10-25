#!/usr/bin/env python3
"""Acceptance check for ticket 03: the vowel-count table in section IX.

Re-derives the vowel-count distribution for both pools from data/answers.txt and
data/allowed.txt, and fails when any cell on the poster drifts.

  * every cell of Fig. 10 matches the re-derived share, for the answers pool and
    for all valid words (answers + allowed guesses);
  * the 3+ row really is the roll-up of the rows above it, not an independent
    figure that can disagree;
  * the Y-as-a-vowel card matches the re-derived figures, including that no
    answer is left without a vowel;
  * the table names its denominators, and they are the pool sizes rather than
    section IX's branch sizes or section VIII's repeat counts.

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

VOWEL_SETS = {"aeiou": set("aeiou"), "aeiouy": set("aeiouy")}
MAX_VOWELS = 5
PLAIN = "aeiou"

# <tr><td class="big">LABEL</td><td class="num-col">X%</td><td class="num-col">Y%</td></tr>
ROW_RE = re.compile(
    r'<tr><td class="big">(?P<label>[^<]+)</td>'
    r'<td class="num-col">(?P<answers>[\d.]+)%</td>'
    r'<td class="num-col">(?P<valid>[\d.]+)%</td></tr>'
)
Y_CARD_RE = re.compile(
    r'<div class="shape-row"><span>(?P<label>[^<]+)</span><b>(?P<value>[^<]+)</b></div>'
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
        label: distribution(words, VOWEL_SETS[PLAIN]) for label, words in pools.items()
    }

    if derived["valid"]["total"] != 14855:
        failures.append(
            f"all-valid pool is {derived['valid']['total']}, expected 14855"
        )
    if len(allowed) != 12546:
        failures.append(f"allowed pool is {len(allowed)}, expected 12546")

    # The 3+ row must be the roll-up of the rows above it.
    for label, stats in derived.items():
        rolled = sum(stats["counts"][k] for k in range(3, MAX_VOWELS + 1))
        if rolled != stats["more_than_two"]:
            failures.append(
                f"{label}: 3+ roll-up is {rolled} but more-than-two is "
                f"{stats['more_than_two']}"
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
        rows[match.group("label").strip()] = (
            float(match.group("answers")),
            float(match.group("valid")),
        )

    for count in range(MAX_VOWELS + 1):
        label = str(count)
        if label not in rows:
            if derived["answers"]["shares"][count] or derived["valid"]["shares"][count]:
                failures.append(f"table has no row for {count} vowels")
            continue
        got_answers, got_valid = rows[label]
        want_answers = derived["answers"]["shares"][count]
        want_valid = derived["valid"]["shares"][count]
        if abs(got_answers - want_answers) > 0.05:
            failures.append(
                f"row {count}: answers cell is {got_answers}%, expected {want_answers}%"
            )
        if abs(got_valid - want_valid) > 0.05:
            failures.append(
                f"row {count}: all-valid cell is {got_valid}%, expected {want_valid}%"
            )

    if "3+" not in rows:
        failures.append("table has no 3+ roll-up row")
    else:
        got_answers, got_valid = rows["3+"]
        if abs(got_answers - derived["answers"]["more_than_two_pct"]) > 0.05:
            failures.append(
                f"3+ answers cell is {got_answers}%, expected "
                f"{derived['answers']['more_than_two_pct']}%"
            )
        if abs(got_valid - derived["valid"]["more_than_two_pct"]) > 0.05:
            failures.append(
                f"3+ all-valid cell is {got_valid}%, expected "
                f"{derived['valid']['more_than_two_pct']}%"
            )

    # --- the Y card ----------------------------------------------------------
    y_stats = {
        label: distribution(words, VOWEL_SETS["aeiouy"])
        for label, words in pools.items()
    }
    card = {
        m.group("label").strip(): m.group("value").strip()
        for m in Y_CARD_RE.finditer(section)
    }
    expected_card = {
        "answers with 3 or more vowels": f"{y_stats['answers']['more_than_two_pct']}%",
        "valid words with 3 or more vowels": f"{y_stats['valid']['more_than_two_pct']}%",
        "answers with no vowel at all": str(y_stats["answers"]["counts"][0]),
    }
    for label, want in expected_card.items():
        got = card.get(label)
        if got is None:
            failures.append(f"Y card has no row {label!r}")
        elif got != want:
            failures.append(f"Y card row {label!r} says {got}, expected {want}")

    # --- denominators --------------------------------------------------------
    for figure in ("2,309", "14,855", "12,546"):
        if figure not in text:
            failures.append(f"table does not name the denominator {figure}")
    if "each pool's own size" not in text:
        failures.append("table does not say its shares use each pool's own size")
    if "Counting A E I O U" not in text:
        failures.append("table does not name the counting convention")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    for label, stats in derived.items():
        cells = ", ".join(
            f"{count}:{stats['shares'][count]}%" for count in range(MAX_VOWELS + 1)
        )
        print(f"  {label:8} ({stats['total']:5}) {cells}")
        print(
            f"  {'':8} 3 or more: {stats['more_than_two']} ({stats['more_than_two_pct']}%)"
        )
    print(
        f"  counting Y: answers 3+ {y_stats['answers']['more_than_two_pct']}%, "
        f"valid 3+ {y_stats['valid']['more_than_two_pct']}%, "
        f"answers with no vowel {y_stats['answers']['counts'][0]}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"FAIL\n  - {exc}")
        sys.exit(1)
