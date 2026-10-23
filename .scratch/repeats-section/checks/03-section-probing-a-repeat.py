#!/usr/bin/env python3
"""Acceptance check for ticket 03: section VIII, "what to do about a repeat".

Re-derives the shape-template strip from data/answers.txt and fails when any
figure drifts, then checks the two-copy probe rule moved cleanly:

  * the strip shows the three commonest repeat shapes as templates with the
    repeated slots marked, sharing the repeated-letter-instance denominator
    (and naming the grid's repeat-pair denominator so the two agree);
  * the probe rule appears exactly once in the poster, inside section VIII,
    with its worked Radar / SOARE / ABACK example intact;
  * section VII points at the rule instead of restating it.

Run: python3 .scratch/repeats-section/checks/03-section-probing-a-repeat.py

For a negative test, point POSTER_PATH at a mutated copy:

  POSTER_PATH=/tmp/mutated.html python3 .scratch/repeats-section/checks/03-section-probing-a-repeat.py
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

# Distinctive fragments of the two-copy probe rule. Each must occur exactly
# once in the whole poster, and that single home is section VIII.
RULE_MARKERS = (
    "guess must carry that letter twice",
    "non-gray tiles among those two copies",
    "copies in the answer",
)
WORKED_EXAMPLE = "both A tiles come back non-gray"

# <span class="tpl" ...>TEMPLATE</span> <span>slots A &amp; B — kind</span>...</span><b>SHARE%</b>
TEMPLATE_RE = re.compile(
    r'<span class="tpl"[^>]*>(?P<tpl>.*?)</span>'
    r'\s*<span>slots (?P<a>\d) &amp; (?P<b>\d)[^<]*</span>'
    r'.*?<b>(?P<share>[\d.]+)%</b>',
    re.DOTALL,
)


def load_answers() -> list[str]:
    return [
        line.strip().lower()
        for line in ANSWERS_PATH.read_text().splitlines()
        if line.strip()
    ]


def shape_counts(words: list[str]) -> Counter[tuple[int, ...]]:
    """Count repeated-letter instances by their slot tuple (mirrors ticket 01)."""
    shapes: Counter[tuple[int, ...]] = Counter()
    for word in words:
        positions: dict[str, list[int]] = {}
        for index, letter in enumerate(word):
            positions.setdefault(letter, []).append(index + 1)
        for slots in positions.values():
            if len(slots) >= 2:
                shapes[tuple(slots)] += 1
    return shapes


def share(part: int, whole: int) -> float:
    return round(100 * part / whole, 1)


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    return html[start : html.index("</section>", start)]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def templates_in(section: str) -> dict[tuple[int, int], tuple[float, tuple[int, ...]]]:
    found: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
    for match in TEMPLATE_RE.finditer(section):
        a, b = int(match.group("a")), int(match.group("b"))
        marked = tuple(
            index + 1
            for index, token in enumerate(clean(match.group("tpl")).split())
            if token == "●"
        )
        found[(a, b)] = (float(match.group("share")), marked)
    return found


def main() -> int:
    failures: list[str] = []
    words = load_answers()
    shapes = shape_counts(words)
    total = sum(shapes.values())
    top3 = sorted(shapes.items(), key=lambda item: (-item[1], item[0]))[:3]

    expected_shapes = {tuple(slots): count for slots, count in top3}
    if expected_shapes != {(3, 4): 186, (1, 5): 91, (2, 5): 87}:
        failures.append(f"re-derived top shapes are {expected_shapes}, expected 3-4/1-5/2-5")
    if total != 786:
        failures.append(f"repeated-letter-instance denominator is {total}, expected 786")
    if [tuple(slots) for slots, _ in top3] != [(3, 4), (1, 5), (2, 5)]:
        failures.append(f"top three shapes are {[s for s, _ in top3]}, expected 3-4, 1-5, 2-5")

    html = POSTER_PATH.read_text()
    if 'id="repeats"' not in html or 'id="shape"' not in html:
        print("FAIL")
        print('  - poster is missing section id="shape" or id="repeats"')
        return 1
    repeats = get_section(html, "repeats")
    shape_section = get_section(html, "shape")
    repeats_text = clean(repeats)
    shape_text = clean(shape_section)

    # --- shape-template strip ----------------------------------------------
    templates = templates_in(repeats)
    for (a, b), count in expected_shapes.items():
        expected_share = share(count, total)
        if (a, b) not in templates:
            failures.append(f"strip has no template for slots {a}-{b}")
            continue
        got_share, marked = templates[(a, b)]
        if got_share != expected_share:
            failures.append(
                f"template {a}-{b} states {got_share}%, expected {expected_share}%"
            )
        if marked != (a, b):
            failures.append(
                f"template {a}-{b} marks slots {marked}, expected {(a, b)}"
            )
        if str(count) not in repeats_text:
            failures.append(f"strip does not state the count {count} for {a}-{b}")
    if len(templates) != 3:
        failures.append(f"strip has {len(templates)} templates, expected exactly 3")

    # Denominator must be the instance count, with the grid's pair count named
    # alongside it so the two figures stay consistent.
    if f"{total} repeated-letter instances" not in repeats_text:
        failures.append("strip does not name the repeated-letter-instance denominator")
    if "826 repeat pairs" not in repeats_text:
        failures.append("strip does not name the grid's repeat-pair denominator")
    if "●" not in repeats or "repeated letter" not in repeats_text:
        failures.append("strip does not explain the repeated-slot marker")

    # --- the probe rule lives here, exactly once ---------------------------
    lowered = html.lower()
    for marker in RULE_MARKERS:
        occurrences = lowered.count(marker.lower())
        if occurrences != 1:
            failures.append(
                f"rule marker {marker!r} appears {occurrences} time(s), expected 1"
            )
        if marker.lower() not in repeats.lower():
            failures.append(f"rule marker {marker!r} is not in section VIII")
    if WORKED_EXAMPLE.lower() not in repeats.lower():
        failures.append("worked example ('both A tiles come back non-gray') is missing")
    for word in ("radar", "soare", "aback"):
        if word not in repeats.lower():
            failures.append(f"worked example is missing the word {word.upper()}")

    # --- section VII cross-references instead of restating ------------------
    if "viii" not in shape_text.lower():
        failures.append("section VII does not cross-reference section VIII")
    for marker in RULE_MARKERS:
        if marker.lower() in shape_text.lower():
            failures.append(
                f"section VII still restates the rule ({marker!r})"
            )

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    for (a, b), count in expected_shapes.items():
        print(f"  template {a}-{b}: {count} of {total} ({share(count, total)}%)")
    print("  probe rule appears once, in section VIII; section VII cross-references it")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"FAIL\n  - {exc}")
        sys.exit(1)
