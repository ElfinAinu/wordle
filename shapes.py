# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Word-shape analysis of the past-answers list.

Vowel counts and where vowels sit, plus consonant/vowel starts and ends.
Vowels = AEIOU; Y reported separately because it behaves as a word-ender.
"""

from collections import Counter

from analyze import ANSWERS_PATH, RESULTS_DIR, load_words

VOWELS = set("aeiou")


def vowel_shapes(answers: list[str]) -> dict:
    count_dist = Counter()
    positions_by_count: dict[int, Counter] = {}
    for word in answers:
        slots = [i + 1 for i, ch in enumerate(word) if ch in VOWELS]
        count_dist[len(slots)] += 1
        positions_by_count.setdefault(len(slots), Counter())[tuple(slots)] += 1
    total = len(answers)
    return {
        "count_pct": {
            k: round(100 * v / total, 1) for k, v in sorted(count_dist.items())
        },
        "positions": {
            str(count): [
                ("".join(map(str, slots)), round(100 * n / count_dist[count], 1))
                for slots, n in counter.most_common(5)
            ]
            for count, counter in sorted(positions_by_count.items())
        },
    }


def edge_letters(answers: list[str]) -> dict:
    groups = {
        "consonant_start": Counter(w[0] for w in answers if w[0] not in VOWELS),
        "consonant_end": Counter(w[-1] for w in answers if w[-1] not in VOWELS),
        "vowel_start": Counter(w[0] for w in answers if w[0] in VOWELS),
        "vowel_end": Counter(w[-1] for w in answers if w[-1] in VOWELS),
        "y_end": Counter(w[-1] for w in answers if w[-1] == "y"),
    }
    total = len(answers)
    return {
        name: [(ch, round(100 * n / total, 1)) for ch, n in counter.most_common(5)]
        for name, counter in groups.items()
    }


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    shapes = vowel_shapes(answers)
    edges = edge_letters(answers)

    lines = [f"# Word shapes ({len(answers)} past answers)", ""]
    lines.append("## Vowel count")
    lines.append(", ".join(f"{k}: {v}%" for k, v in shapes["count_pct"].items()))
    lines.append("")
    lines.append("## Vowel positions (slots, share within count)")
    for count, top in shapes["positions"].items():
        lines.append(
            f"- {count} vowels: " + ", ".join(f"[{slots}] {pct}%" for slots, pct in top)
        )
    lines.append("")
    lines.append("## Edges (share of all answers)")
    for name, top in edges.items():
        lines.append(
            f"- {name}: " + ", ".join(f"{ch.upper()} {pct}%" for ch, pct in top)
        )
    lines.append("")

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "shapes.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
