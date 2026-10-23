# /// script
# requires-python = ">=3.11"
# ///
"""Acceptance check for ticket 05 (doubles guidance in the mistakes panel).

Recomputes the repeat figures from data/answers.txt and asserts the deployed
poster infographic-v4.html carries them, separates adjacent doubles from
repeats overall, keeps the two-copy rule in section VIII with section VII
cross-referencing it, and gives a worked vowel-apart example that the fixed
two-opener cannot see.

Run: python3 .scratch/poster-fixes/checks/05-doubles-guidance.py
"""

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANSWERS = ROOT / "data" / "answers.txt"
POSTER = ROOT / "infographic-v4.html"

VOWELS = set("aeiou")
WORD_LENGTH = 5


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    return html[start : html.index("</section>", start)]


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def vowel_apart_repeat(word: str) -> bool:
    counts = Counter(word)
    touching = {word[i] for i in range(WORD_LENGTH - 1) if word[i] == word[i + 1]}
    return any(
        count >= 2 and ch in VOWELS and ch not in touching
        for ch, count in counts.items()
    )


def figures(words):
    total = len(words)
    any_repeat = sum(1 for w in words if len(set(w)) < WORD_LENGTH)
    adjacent = sum(1 for w in words if any(w[i] == w[i + 1] for i in range(4)))
    vowel_apart = sum(1 for w in words if vowel_apart_repeat(w))
    return {
        "total": total,
        "any_repeat": round(100 * any_repeat / total, 1),
        "adjacent": round(100 * adjacent / total, 1),
        "vowel_apart": round(100 * vowel_apart / total, 1),
    }


def main():
    words = [w.strip() for w in ANSWERS.read_text().split() if w.strip()]
    stats = figures(words)

    assert stats["any_repeat"] == 32.4, stats
    assert stats["adjacent"] == 14.7, stats
    assert stats["vowel_apart"] == 10.3, stats

    html = POSTER.read_text()
    lowered = html.lower()

    # The panel carries the wider figure and keeps adjacent doubles distinct.
    for quoted in ("32.4%", "14.7%", "10.3%"):
        assert quoted in html, f"poster is missing quoted figure {quoted}"
    assert "adjacent" in lowered, "poster does not name the adjacent kind"

    # The two-copy rule now lives in section VIII (ticket 03), stated as an
    # action; section VII points at it instead of restating it.
    repeats = get_section(html, "repeats")
    repeats_lowered = repeats.lower()
    shape = get_section(html, "shape")
    shape_text = clean(shape).lower()
    assert "twice" in repeats_lowered, "two-copy rule missing 'twice'"
    assert "non-gray" in repeats_lowered, "two-copy rule missing the non-gray count"
    assert (
        "copies in the answer" in repeats_lowered
    ), "two-copy rule missing the count meaning"
    assert "viii" in shape_text, "section VII does not cross-reference section VIII"
    assert (
        "copies in the answer" not in shape_text
    ), "section VII still restates the two-copy rule"

    # One worked example that is real and really is an invisible vowel-apart repeat.
    examples = [w for w in ("radar", "tenet") if w in words and w in repeats_lowered]
    assert examples, "no verified worked vowel-apart example in the poster"
    for word in examples:
        assert vowel_apart_repeat(word), f"{word} is not a vowel-apart repeat"

    print(
        f"OK: {stats['total']} answers; any repeat {stats['any_repeat']}%, "
        f"adjacent {stats['adjacent']}%, vowel-apart {stats['vowel_apart']}%; "
        f"worked example(s): {', '.join(examples)}"
    )


if __name__ == "__main__":
    main()
