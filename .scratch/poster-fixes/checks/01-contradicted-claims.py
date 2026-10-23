#!/usr/bin/env python3
"""Ticket 01 check: the hero and five-hit tier must not contradict the board.

Recomputes the two affected figures from data/answers.txt with pure Python,
then asserts the deployed poster (infographic-v4.html) states them correctly.

Run: python3 .scratch/poster-fixes/checks/01-contradicted-claims.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANSWERS_PATH = ROOT / "data" / "answers.txt"
POSTER_PATH = ROOT / "infographic-v4.html"

SOARE = "soare"
CLINT = "clint"
ANAGRAM_PAIRS = {frozenset({"arise", "raise"}), frozenset({"resin", "risen"})}


def feedback(guess: str, answer: str) -> str:
    result = ["X"] * 5
    remaining: dict[str, int] = {}
    for guess_letter, answer_letter, i in zip(guess, answer, range(5)):
        if guess_letter == answer_letter:
            result[i] = "G"
        else:
            remaining[answer_letter] = remaining.get(answer_letter, 0) + 1
    for i, guess_letter in enumerate(guess):
        if result[i] == "G":
            continue
        if remaining.get(guess_letter, 0) > 0:
            result[i] = "Y"
            remaining[guess_letter] -= 1
    return "".join(result)


def hits(combined: tuple[str, str]) -> int:
    return sum(part.count("G") + part.count("Y") for part in combined)


def recompute() -> dict:
    answers = [
        word.strip().lower()
        for word in ANSWERS_PATH.read_text().split()
        if word.strip()
    ]
    groups: dict[tuple[str, str], list[str]] = {}
    for answer in answers:
        key = (feedback(SOARE, answer), feedback(CLINT, answer))
        groups.setdefault(key, []).append(answer)

    pinned_games = sum(len(words) for words in groups.values() if len(words) == 1)
    pinned_pct = round(100 * pinned_games / len(answers), 2)

    five_hit_ties = [
        frozenset(words)
        for key, words in groups.items()
        if hits(key) == 5 and len(words) > 1
    ]
    tied_games = sum(
        len(words) for key, words in groups.items() if hits(key) == 5 and len(words) > 1
    )
    return {
        "total": len(answers),
        "has_soare": SOARE in answers,
        "has_clint": CLINT in answers,
        "pinned_pct": pinned_pct,
        "five_hit_ties": set(five_hit_ties),
        "tied_games": tied_games,
    }


def five_hit_card(html: str) -> str:
    start = html.index("<h3>5 hits")
    end = html.index("</div>", html.index("</table>", start))
    return html[start:end]


def main() -> int:
    data = recompute()
    failures: list[str] = []

    # --- figures recomputed from data/answers.txt -------------------------
    if data["total"] != 2309:
        failures.append(f"answer pool is {data['total']}, expected 2309")
    if data["has_soare"]:
        failures.append("SOARE is present in answers.txt; it must never be the answer")
    if data["has_clint"]:
        failures.append("CLINT is present in answers.txt; it must never be the answer")
    if data["pinned_pct"] != 27.76:
        failures.append(
            f"share pinned before guess three is {data['pinned_pct']}%, expected 27.76%"
        )
    if data["five_hit_ties"] != ANAGRAM_PAIRS:
        failures.append(
            f"five-hit multi-candidate groups are {data['five_hit_ties']}, "
            f"expected {ANAGRAM_PAIRS}"
        )
    if data["tied_games"] != 4:
        failures.append(f"{data['tied_games']} games end in a five-hit tie, expected 4")

    html = POSTER_PATH.read_text()
    if re.search(r"solved on the second guess", html, re.IGNORECASE):
        failures.append("hero still claims games are solved on the second guess")
    if not re.search(r"pinned before guess three", html, re.IGNORECASE):
        failures.append("hero does not say the answer is pinned before guess three")
    if re.search(r"answer is confirmed", html, re.IGNORECASE):
        failures.append("five-hit tier still claims the answer is confirmed")

    card = five_hit_card(html).lower()
    for word in ("arise", "raise", "resin", "risen"):
        if word not in card:
            failures.append(f"five-hit tier does not name {word.upper()}")
    if "2309" not in card and "2,309" not in card:
        failures.append("five-hit tier does not cite 4 of 2,309 games")
    if not re.search(r"either|other", card):
        failures.append("five-hit tier does not say how to pick between the pair")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    print(f"  pool={data['total']} answers, SOARE/CLINT absent")
    print(f"  pinned before guess three: {data['pinned_pct']}%")
    print(f"  five-hit anagram ties: {sorted(map(sorted, data['five_hit_ties']))}")
    print(f"  games in a five-hit tie: {data['tied_games']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
