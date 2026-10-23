"""Acceptance check for ticket 05 (doubles guidance in the mistakes panel).

Recomputes the repeat figures from data/answers.txt and asserts the deployed
poster infographic-v4.html carries them, separates adjacent doubles from
repeats overall, states the two-copy rule, and gives a worked vowel-apart
example that the fixed two-opener cannot see.

Run: python3 check_doubles_guidance.py
"""

from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANSWERS = ROOT / "data" / "answers.txt"
POSTER = ROOT / "infographic-v4.html"

VOWELS = set("aeiou")
WORD_LENGTH = 5


def figures(words):
    total = len(words)
    any_repeat = sum(1 for w in words if len(set(w)) < WORD_LENGTH)
    adjacent = sum(1 for w in words if any(w[i] == w[i + 1] for i in range(4)))
    vowel_apart = 0
    for word in words:
        counts = Counter(word)
        touching = {word[i] for i in range(4) if word[i] == word[i + 1]}
        if any(
            count >= 2 and ch in VOWELS and ch not in touching
            for ch, count in counts.items()
        ):
            vowel_apart += 1
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

    # The panel carries the wider figure and keeps adjacent doubles distinct.
    for quoted in ("32.4%", "14.7%", "10.3%"):
        assert quoted in html, f"poster is missing quoted figure {quoted}"
    assert "adjacent" in html.lower(), "poster does not name the adjacent kind"

    # The two-copy rule is stated as an action.
    lowered = html.lower()
    assert "twice" in lowered, "two-copy rule missing 'twice'"
    assert "non-gray" in lowered, "two-copy rule missing the non-gray count"
    assert "copies in the answer" in lowered, "two-copy rule missing the count meaning"

    # One worked example that is real and really is an invisible vowel-apart repeat.
    examples = [w for w in ("radar", "tenet") if w in words and w in lowered]
    assert examples, "no verified worked vowel-apart example in the poster"
    for word in examples:
        counts = Counter(word)
        touching = {word[i] for i in range(4) if word[i] == word[i + 1]}
        assert any(
            counts[ch] >= 2 and ch in VOWELS and ch not in touching for ch in counts
        ), f"{word} is not a vowel-apart repeat"

    print(
        f"OK: {stats['total']} answers; any repeat {stats['any_repeat']}%, "
        f"adjacent {stats['adjacent']}%, vowel-apart {stats['vowel_apart']}%; "
        f"worked example(s): {', '.join(examples)}"
    )


if __name__ == "__main__":
    main()
