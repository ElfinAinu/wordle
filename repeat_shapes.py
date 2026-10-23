# /// script
# requires-python = ">=3.11"
# ///
"""Where letter repeats sit in the Wordle answer list, and whether they show.

`duplicates.py` answers how often letters repeat. This answers the follow-up:
which slot pairs carry the repeats, what shape a repeated letter takes, whether
touching repeats skew by letter class, and whether the fixed two-opener
(SOARE + CLINT) could have revealed the repeat at all.

Universe: the 2309 committed answers in data/answers.txt.
Opening pair: SOARE + CLINT, the fixed opening taught by the poster
(mirrors hit_tree.PAIR).

Outputs results/repeat_shapes.md and results/repeat_shapes.json. Regenerating
twice produces identical files.
"""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
ANSWERS_PATH = ROOT / "data" / "answers.txt"
RESULTS_DIR = ROOT / "results"

WORD_LENGTH = 5
VOWELS = set("aeiou")
# The fixed opening: SOARE then CLINT. Kept literal so this script stays
# standard-library only; it mirrors hit_tree.PAIR.
OPENING = ("soare", "clint")
OPENING_LETTERS = set("".join(OPENING))


def load_words(path: Path) -> list[str]:
    return [
        line.strip().lower() for line in path.read_text().splitlines() if line.strip()
    ]


def letter_class(letter: str) -> str:
    if letter in VOWELS:
        return "vowel"
    return "y" if letter == "y" else "consonant"


def share(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def analyse(words: list[str]) -> dict:
    repeat_words = 0
    pair_counts: Counter[tuple[int, int]] = Counter()
    shape_counts: Counter[tuple[int, ...]] = Counter()
    touching_class: Counter[str] = Counter()
    separated_class: Counter[str] = Counter()
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
            shape_counts[tuple(slots)] += 1
            if touching:
                touching_class[letter_class(letter)] += 1
            else:
                separated_class[letter_class(letter)] += 1
            if letter in OPENING_LETTERS:
                tested += 1
            else:
                untested += 1

    total = len(words)
    instances = sum(shape_counts.values())
    pairs = sum(pair_counts.values())
    touching_total = sum(touching_class.values())
    separated_total = sum(separated_class.values())

    slot_pairs = [
        {
            "pair": f"{a}-{b}",
            "slots": [a, b],
            "count": count,
            "share_pct": share(count, pairs),
            "touching": b - a == 1,
        }
        for (a, b), count in sorted(
            pair_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]

    shapes = [
        {
            "slots": ",".join(str(slot) for slot in slots),
            "count": count,
            "touching": any(
                slots[i + 1] - slots[i] == 1 for i in range(len(slots) - 1)
            ),
        }
        for slots, count in sorted(
            shape_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]

    def by_class(counts: Counter[str], whole: int) -> dict:
        return {
            kind: {
                "count": counts.get(kind, 0),
                "share_pct": share(counts.get(kind, 0), whole),
            }
            for kind in ("vowel", "consonant", "y")
        }

    return {
        "universe": {
            "path": "data/answers.txt",
            "words": total,
            "description": "the committed Wordle answer list",
        },
        "opening": {
            "pair": [word.upper() for word in OPENING],
            "letters": "".join(sorted(OPENING_LETTERS)),
            "description": "the poster's fixed two-opener; its ten letters are tested",
        },
        "repeat_words": repeat_words,
        "repeat_word_pct": share(repeat_words, total),
        "repeated_letter_instances": instances,
        "repeat_pairs": pairs,
        "slot_pairs": {
            "denominator": pairs,
            "denominator_note": "repeat pairs: a letter used n times contributes n(n-1)/2",
            "rows": slot_pairs,
        },
        "shapes": {
            "denominator": instances,
            "denominator_note": "repeated-letter instances: one per repeated letter per word",
            "rows": shapes,
        },
        "class_split": {
            "denominator": instances,
            "denominator_note": "repeated-letter instances",
            "touching": {
                "denominator": touching_total,
                "by_class": by_class(touching_class, touching_total),
            },
            "separated": {
                "denominator": separated_total,
                "by_class": by_class(separated_class, separated_total),
            },
        },
        "visibility": {
            "denominator": instances,
            "denominator_note": "repeated-letter instances",
            "tested": {
                "count": tested,
                "share_pct": share(tested, instances),
                "description": "repeat a letter the opening tests: one copy can show, the count cannot be read",
            },
            "untested": {
                "count": untested,
                "share_pct": share(untested, instances),
                "description": "repeat a letter the opening never tests: nothing shows at all",
            },
        },
    }


def write_markdown(stats: dict, path: Path) -> None:
    opening = stats["opening"]
    universe = stats["universe"]
    lines = [
        "# How Wordle repeats are shaped",
        "",
        f"Universe: {universe['path']} ({universe['words']} answers), "
        f"{stats['repeat_words']} of them ({stats['repeat_word_pct']}%) contain a repeat.",
        f"Opening pair: {' + '.join(opening['pair'])} "
        f"({opening['letters']}); the {len(opening['letters'])} letters it tests are "
        "the visibility reference.",
        "",
        "A *repeat pair* is two copies of one letter; a letter used three times "
        "contributes three pairs. A *repeated-letter instance* is one repeated "
        "letter in one word, counted once however many copies it has.",
        "",
        "## Slot pairs",
        "",
        f"Denominator: {stats['slot_pairs']['denominator']} repeat pairs.",
        "",
        "| pair | count | share | touches |",
        "|---|---|---|---|",
    ]
    for row in stats["slot_pairs"]["rows"]:
        lines.append(
            f"| {row['pair']} | {row['count']} | {row['share_pct']}% | "
            f"{'yes' if row['touching'] else 'no'} |"
        )
    lines.append("")

    lines.append("## Shapes of a repeated letter")
    lines.append("")
    lines.append(
        f"Denominator: {stats['shapes']['denominator']} repeated-letter instances. "
        "Slots are 1-indexed positions in the answer."
    )
    lines.append("")
    lines.append("| slots | count | touching |")
    lines.append("|---|---|---|")
    for row in stats["shapes"]["rows"]:
        lines.append(
            f"| {row['slots']} | {row['count']} | "
            f"{'touching' if row['touching'] else 'separated'} |"
        )
    lines.append("")

    lines.append("## Touching vs separated, by letter class")
    lines.append("")
    lines.append(
        f"Denominator: {stats['class_split']['denominator']} repeated-letter instances "
        f"({stats['class_split']['touching']['denominator']} touching, "
        f"{stats['class_split']['separated']['denominator']} separated)."
    )
    lines.append("")
    lines.append("| kind | vowel | consonant | y |")
    lines.append("|---|---|---|---|")
    for kind in ("touching", "separated"):
        group = stats["class_split"][kind]
        cells = [
            f"{group['by_class'][cls]['count']} ({group['by_class'][cls]['share_pct']}%)"
            for cls in ("vowel", "consonant", "y")
        ]
        lines.append(f"| {kind} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Visibility against the fixed opening")
    lines.append("")
    lines.append(
        f"Denominator: {stats['visibility']['denominator']} repeated-letter instances."
    )
    lines.append("")
    lines.append("| opening tests the repeated letter | instances | share |")
    lines.append("|---|---|---|")
    lines.append(
        f"| yes | {stats['visibility']['tested']['count']} | "
        f"{stats['visibility']['tested']['share_pct']}% |"
    )
    lines.append(
        f"| no | {stats['visibility']['untested']['count']} | "
        f"{stats['visibility']['untested']['share_pct']}% |"
    )
    lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    words = load_words(ANSWERS_PATH)
    stats = analyse(words)

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "repeat_shapes.json").write_text(json.dumps(stats, indent=2))
    write_markdown(stats, RESULTS_DIR / "repeat_shapes.md")

    print(
        f"{stats['repeat_words']} of {stats['universe']['words']} answers "
        f"({stats['repeat_word_pct']}%) repeat a letter; "
        f"{stats['repeated_letter_instances']} repeated-letter instances, "
        f"{stats['repeat_pairs']} repeat pairs"
    )
    print("Wrote results/repeat_shapes.json and results/repeat_shapes.md")


if __name__ == "__main__":
    main()
