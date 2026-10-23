#!/usr/bin/env python3
"""Ticket 07 check: the performance ladder must be honest and traceable.

Reads the ladder section of the shipped poster (infographic-v4.html) and the
taught-method simulation (results/simulate_method.json), then asserts every
acceptance criterion in .scratch/poster-fixes/issues/07-rebuild-ladder.md:

  * no rung is labelled a median;
  * every rung's number is stated by a source named on the panel;
  * the gaps between adjacent rungs agree with the claims the panel makes;
  * the taught method appears with its simulated average;
  * the optimal-policy rung reads as the optimal policy, and the taught
    method's worst case (six, JOKER) is stated rather than a never-more-than-
    five guarantee;
  * the six-guess caveat is present.

Pure Python, no dependencies.

Run: python3 .scratch/poster-fixes/checks/07-rebuild-ladder.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POSTER_PATH = ROOT / "infographic-v4.html"
SIM_PATH = ROOT / "results" / "simulate_method.json"

# Source of truth for each rung: (source keyword that must be named in the
# rung label, value the source states).  The taught-method value is checked
# against results/simulate_method.json instead of a literal.
OPTIMAL_VALUE = 3.421  # MIT/OR, Bertsimas-Paskov, SALET exact solution
HUMAN_SOURCE = "WordsRated"  # 266,000 Reddit-shared games, 3.80 average
HUMAN_VALUE = 3.80
TAUGHT_SOURCE = "simulation"

# The panel prose claims each adjacent gap is "about a fifth of a guess".
GAP_CLAIM = 0.20
GAP_TOLERANCE = 0.03

# Bars are said to scale from 3.0 to 4.0 guesses.
BAR_BASE = 3.0
BAR_TOLERANCE = 2  # percentage points


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    end = html.index("</section>", start)
    return html[start:end]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_rungs(section: str) -> list[dict]:
    rungs = []
    for row in re.findall(r'<div class="lad-row">(.*?)</div>', section, re.S):
        num = re.search(r'<span class="lad-num">\s*([0-9.]+)\s*</span>', row)
        lab = re.search(r'<span class="lad-lab">(.*?)</span>', row, re.S)
        width = re.search(r'style="width:\s*([0-9.]+)%"', row)
        if not (num and lab):
            continue
        rungs.append(
            {
                "value": float(num.group(1)),
                "label": clean(lab.group(1)),
                "raw_label": lab.group(1),
                "width": float(width.group(1)) if width else None,
            }
        )
    return rungs


def find_rung(rungs: list[dict], needle: str) -> dict | None:
    for rung in rungs:
        if needle.lower() in rung["label"].lower():
            return rung
    return None


def main() -> int:
    failures: list[str] = []
    html = POSTER_PATH.read_text()
    section = get_section(html, "ladder")
    text = clean(section)
    lower = text.lower()
    rungs = parse_rungs(section)
    sim = json.loads(SIM_PATH.read_text())
    taught_expected = round(sim["average_guesses"], 2)

    if not rungs:
        print("FAIL")
        print("  - ladder section has no rungs")
        return 1

    # --- no rung is labelled a median ------------------------------------
    if "median" in lower:
        failures.append("a rung or the panel prose is still labelled a median")

    # --- the taught method appears at its simulated average --------------
    taught = find_rung(rungs, "taught method")
    if taught is None:
        failures.append("no rung names the taught method")
    else:
        if abs(taught["value"] - taught_expected) > 1e-9:
            failures.append(
                f"taught-method rung is {taught['value']}, "
                f"expected {taught_expected} from simulate_method.json"
            )
        if TAUGHT_SOURCE not in taught["label"]:
            failures.append(
                "taught-method rung does not name its source "
                f"({TAUGHT_SOURCE!r})"
            )
        if "worst case 6" not in taught["label"].lower():
            failures.append("taught-method rung does not state its worst case of six")

    # --- the optimal rung reads as the optimal policy --------------------
    optimal = find_rung(rungs, "optimal")
    if optimal is None:
        failures.append("no rung is labelled as the optimal policy")
    else:
        if abs(optimal["value"] - round(OPTIMAL_VALUE, 2)) > 1e-9:
            failures.append(
                f"optimal rung is {optimal['value']}, expected {OPTIMAL_VALUE}"
            )
        if "MIT/OR" not in optimal["label"]:
            failures.append("optimal rung does not name the MIT/OR paper")
        if "worst case 5" not in optimal["label"].lower():
            failures.append("optimal rung does not state the five-guess guarantee")
        if "taught" in optimal["label"].lower():
            failures.append("optimal rung conflates itself with the taught method")

    # --- the average-player rung names its source ------------------------
    human = find_rung(rungs, "average player")
    if human is None:
        failures.append("no rung names the average player")
    else:
        if abs(human["value"] - HUMAN_VALUE) > 1e-9:
            failures.append(
                f"average-player rung is {human['value']}, expected {HUMAN_VALUE}"
            )
        if HUMAN_SOURCE not in human["label"]:
            failures.append(
                f"average-player rung does not name its source ({HUMAN_SOURCE!r})"
            )

    # --- no unattributable bot/median numbers remain ---------------------
    if re.search(r"wordlebot users\s*·", lower):
        failures.append("a WordleBot-users rung survives without a stated average")
    for banned in ("3.75", "4.10", "4.50"):
        if banned in text:
            failures.append(f"unattributable rung value {banned} still on the panel")

    # --- gaps between adjacent rungs match the prose claims --------------
    values = sorted(rung["value"] for rung in rungs)
    if values == [3.42, 3.61, 3.80]:
        gaps = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        if any(abs(gap - GAP_CLAIM) > GAP_TOLERANCE for gap in gaps):
            failures.append(f"adjacent-rung gaps {gaps} do not match the claim")
        if "fifth" not in lower:
            failures.append("panel prose does not state the one-fifth gaps")
    else:
        failures.append(f"ladder rung values are {values}, expected [3.42, 3.61, 3.80]")

    if "three-quarters" in lower:
        failures.append("panel still claims a three-quarters gap the rungs deny")

    # --- the sourced relative statement is kept --------------------------
    if "quarter of a turn" not in lower:
        failures.append("the NYT quarter-turn relative statement was dropped")
    if "515" not in text:
        failures.append("the panel does not name the 515-million-game NYT source")

    # --- bars match the stated scale -------------------------------------
    for rung in rungs:
        if rung["width"] is None:
            failures.append(f"rung {rung['value']} has no bar width")
            continue
        expected_width = (rung["value"] - BAR_BASE) * 100
        if abs(rung["width"] - expected_width) > BAR_TOLERANCE:
            failures.append(
                f"rung {rung['value']} bar is {rung['width']}%, "
                f"expected {expected_width:.0f}% for the stated 3.0-4.0 scale"
            )

    # --- the six-guess caveat is present and qualified -------------------
    if "joker" not in lower:
        failures.append("panel does not name the six-guess game JOKER")
    if not re.search(r"one of 2,?309", lower):
        failures.append("panel does not say exactly one of 2,309 games reaches six")
    if "almost always" not in lower or "strategy failure" not in lower:
        failures.append(
            "the six-guess-is-a-strategy-failure point is not qualified as almost always"
        )

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    print(f"  rungs: {[(r['value'], r['label']) for r in rungs]}")
    print(f"  taught-method average matches simulate_method.json ({taught_expected})")
    print("  no median; every rung names its source; gaps match the prose")
    print("  optimal/worst-case split stated; JOKER six-guess caveat present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
