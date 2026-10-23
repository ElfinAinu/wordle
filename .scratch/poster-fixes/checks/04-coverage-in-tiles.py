#!/usr/bin/env python3
"""Ticket 04 check: coverage must be reported in tiles, not only distinct letters.

Recomputes both coverage figures and the two letter-grid exceptions straight
from data/answers.txt, then asserts the coverage outputs and the shipped poster
(infographic-v4.html) state them.

Run: python3 .scratch/poster-fixes/checks/04-coverage-in-tiles.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANSWERS_PATH = ROOT / "data" / "answers.txt"
POSTER_PATH = ROOT / "infographic-v4.html"
COVERAGE_JSON = ROOT / "results" / "coverage.json"
COVERAGE_MD = ROOT / "results" / "coverage.md"

PAIR = ("soare", "clint")
PAIR_LETTERS = set("".join(PAIR))
EXPECTED_DISTINCT_PCT = 65.4
EXPECTED_TILES_PCT = 60.9
# The two slots an answer occupies but that round to 0.0% at one decimal.
EXPECTED_EXCEPTIONS = {("q", 2): "pique", ("u", 4): "bayou"}


def load_answers() -> list[str]:
    return [
        line.strip().lower()
        for line in ANSWERS_PATH.read_text().splitlines()
        if line.strip()
    ]


def coverage(answers: list[str]) -> tuple[float, float]:
    """Mean distinct-letter share and mean tiles-lit share for the fixed pair."""
    distinct = 0.0
    tiles = 0.0
    for word in answers:
        overlap = sum(1 for ch in set(word) if ch in PAIR_LETTERS)
        distinct += overlap / len(set(word))
        tiles += overlap / 5.0
    return 100 * distinct / len(answers), 100 * tiles / len(answers)


def slot_count(answers: list[str], letter: str, pos: int) -> int:
    return sum(1 for word in answers if word[pos] == letter)


def section(html: str, start_marker: str) -> str:
    start = html.index(start_marker)
    return html[start : html.index("</section>", start)]


def parse_cells(grid_html: str) -> dict[tuple[str, int], str]:
    """Map (letter, 0-based pos) -> rendered cell text."""
    cells: dict[tuple[str, int], str] = {}
    for match in re.finditer(
        r'<span class="hm-cell"[^>]*title="([A-Z]) @ pos (\d):[^"]*"[^>]*>(.*?)</span>',
        grid_html,
    ):
        letter, pos, text = (
            match.group(1).lower(),
            int(match.group(2)) - 1,
            match.group(3),
        )
        cells[(letter, pos)] = text
    return cells


def main() -> int:
    failures: list[str] = []
    answers = load_answers()
    total = len(answers)

    distinct_pct, tiles_pct = coverage(answers)
    if round(distinct_pct, 1) != EXPECTED_DISTINCT_PCT:
        failures.append(
            f"distinct-letter share is {distinct_pct:.2f}%, expected {EXPECTED_DISTINCT_PCT}%"
        )
    if round(tiles_pct, 1) != EXPECTED_TILES_PCT:
        failures.append(
            f"tiles-lit share is {tiles_pct:.2f}%, expected {EXPECTED_TILES_PCT}%"
        )
    if tiles_pct >= distinct_pct:
        failures.append("tiles-lit share should be below the distinct-letter share")

    # --- the two grid exceptions, from the raw answers -------------------
    for (letter, pos), word in EXPECTED_EXCEPTIONS.items():
        hits = [w for w in answers if w[pos] == letter]
        if hits != [word]:
            failures.append(
                f"{letter.upper()} @ pos {pos + 1} is {hits}, expected only {word.upper()}"
            )

    # Slots that hold a letter but round to an impossible-looking 0.0%.
    rounded_impossible = {
        (chr(97 + letter), pos)
        for letter in range(26)
        for pos in range(5)
        if slot_count(answers, chr(97 + letter), pos) > 0
        and round(100 * slot_count(answers, chr(97 + letter), pos) / total, 1) == 0.0
    }
    if rounded_impossible != set(EXPECTED_EXCEPTIONS):
        failures.append(
            f"slots that round to 0.0% but are possible: {rounded_impossible}, "
            f"expected {set(EXPECTED_EXCEPTIONS)}"
        )

    # --- coverage analysis reports both numbers --------------------------
    if not COVERAGE_JSON.exists():
        failures.append("results/coverage.json is missing")
    else:
        rows = json.loads(COVERAGE_JSON.read_text())
        if not rows:
            failures.append("results/coverage.json has no rows")
        else:
            if "tiles_lit_pct" not in rows[0]:
                failures.append("coverage.json rows lack the tiles-lit figure")
            if "spot_rate_pct" not in rows[0]:
                failures.append("coverage.json rows lack the distinct-letter figure")
            for row in rows:
                pair_letters = set(row["first"] + row["second"])
                d = sum(
                    sum(1 for ch in set(w) if ch in pair_letters) / len(set(w))
                    for w in answers
                )
                t = sum(
                    sum(1 for ch in set(w) if ch in pair_letters) / 5.0 for w in answers
                )
                if abs(100 * d / total - row["spot_rate_pct"]) > 0.06:
                    failures.append(
                        f"coverage.json spot rate wrong for {row['first']}+{row['second']}"
                    )
                if abs(100 * t / total - row.get("tiles_lit_pct", -1)) > 0.06:
                    failures.append(
                        f"coverage.json tiles rate wrong for {row['first']}+{row['second']}"
                    )

    if not COVERAGE_MD.exists():
        failures.append("results/coverage.md is missing")
    else:
        md = COVERAGE_MD.read_text()
        header = md.splitlines()[2].lower() if len(md.splitlines()) > 2 else ""
        if "distinct" not in header:
            failures.append(
                "coverage.md header does not name the distinct-letter figure"
            )
        if "tile" not in header:
            failures.append("coverage.md header does not name the tiles-lit figure")

    # --- the shipped poster names the metric it uses ---------------------
    html = POSTER_PATH.read_text()
    hero = section(html, '<section class="hero')
    method = section(html, '<section class="section" id="method"')

    for name, chunk in (("hero", hero), ("Fig. 01 opener figure", method)):
        if "60.9" not in chunk:
            failures.append(f"{name} does not lead with the tiles-lit figure (60.9%)")
        if "tiles" not in chunk.lower() and "tile" not in chunk.lower():
            failures.append(f"{name} does not name the tiles metric in words")
        if "65.4" not in chunk:
            failures.append(f"{name} does not name the distinct-letter figure (65.4%)")

    # --- no possible slot is drawn as the impossible glyph ---------------
    grid = section(html, '<section class="section" id="grid"')
    cells = parse_cells(grid)
    for letter in range(26):
        ch = chr(97 + letter)
        for pos in range(5):
            if slot_count(answers, ch, pos) == 0:
                continue
            text = cells.get((ch, pos))
            if text is None:
                failures.append(f"grid has no cell for {ch.upper()} @ pos {pos + 1}")
            elif "·" in text:
                failures.append(
                    f"{ch.upper()} @ pos {pos + 1} is drawn impossible though answers put it there"
                )

    for (letter, pos), word in EXPECTED_EXCEPTIONS.items():
        text = cells.get((letter, pos), "")
        if "·" in text:
            failures.append(
                f"{letter.upper()} @ pos {pos + 1} still uses the impossible glyph"
            )
        cell_html = re.search(
            rf'<span class="hm-cell"[^>]*title="{letter.upper()} @ pos {pos + 1}:[^"]*"[^>]*>.*?</span>',
            grid,
        )
        if cell_html is None or word.upper() not in cell_html.group(0):
            failures.append(
                f"{letter.upper()} @ pos {pos + 1} does not make {word.upper()} visible"
            )

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    print(f"  distinct-letter share: {distinct_pct:.2f}%")
    print(f"  tiles-lit share:       {tiles_pct:.2f}%")
    print(f"  grid exceptions:       PIQUE (Q @ 3), BAYOU (U @ 5), 1 of {total} each")
    return 0


if __name__ == "__main__":
    sys.exit(main())
