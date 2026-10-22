# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Duplicate-letter analysis of the Wordle word pools.

Two repeat kinds, because they behave differently:
  adjacent     - the two copies touch ("teeth", "geese")
  non-adjacent - separated by other letters ("radar", "aback", "cacao")

Run over three pools: answers, bonus allowed guesses, and their union.
"""

import json
from collections import Counter

from analyze import ALLOWED_PATH, ANSWERS_PATH, RESULTS_DIR, load_words

VOWELS = set("aeiou")
WORD_LENGTH = 5


def letter_class(letter: str) -> str:
    if letter in VOWELS:
        return "vowel"
    return "y" if letter == "y" else "consonant"


def touching_pairs(word: str) -> set[str]:
    return {word[i] for i in range(WORD_LENGTH - 1) if word[i] == word[i + 1]}


def pool_stats(words: list[str]) -> dict:
    total = len(words)
    distinct_dist = Counter(len(set(word)) for word in words)

    repeat_words = [word for word in words if len(set(word)) < WORD_LENGTH]
    adjacent_words = [word for word in words if touching_pairs(word)]

    repeat_instances = Counter()
    adjacent_instances = Counter()
    repeated_letters = Counter()
    letter_mix = Counter()
    vowel_apart_words = 0

    for word in words:
        counts = Counter(word)
        letter_mix.update(letter_class(ch) for ch in word)
        touching = touching_pairs(word)
        apart_vowel = False
        for letter, count in counts.items():
            if count < 2:
                continue
            kind = letter_class(letter)
            repeat_instances[kind] += 1
            repeated_letters[letter] += 1
            if letter in touching:
                adjacent_instances[kind] += 1
            elif kind == "vowel":
                apart_vowel = True
        vowel_apart_words += apart_vowel

    repeat_total = sum(repeat_instances.values())
    letter_total = sum(letter_mix.values())

    return {
        "total": total,
        "distinct_pct": {
            str(k): round(100 * v / total, 1) for k, v in sorted(distinct_dist.items())
        },
        "any_repeat_pct": round(100 * len(repeat_words) / total, 1),
        "adjacent_word_pct": round(100 * len(adjacent_words) / total, 1),
        "vowel_apart_word_pct": round(100 * vowel_apart_words / total, 1),
        "repeat_instances": dict(repeat_instances),
        "adjacent_instances": dict(adjacent_instances),
        "repeat_instance_pct": {
            kind: round(100 * n / repeat_total, 1)
            for kind, n in repeat_instances.items()
        },
        "baseline_letter_pct": {
            kind: round(100 * n / letter_total, 1) for kind, n in letter_mix.items()
        },
        "top_repeated_letters": [[ch, n] for ch, n in repeated_letters.most_common()][
            :12
        ],
        "triple_plus": sum(1 for word in words if max(Counter(word).values()) >= 3),
        "two_pairs": sum(
            1
            for word in words
            if len(set(word)) == 3 and max(Counter(word).values()) == 2
        ),
        "y_repeat_words": sorted(word for word in words if Counter(word)["y"] > 1),
    }


def ratio(part: float, whole: float) -> float:
    return round(part / whole, 2) if whole else 0.0


def write_markdown(pools: dict[str, dict], path) -> None:
    lines = ["# Duplicate letters in the Wordle pools", ""]
    lines.append(
        "| pool | words | any repeat | adjacent double | repeat a vowel apart |"
    )
    lines.append("|---|---|---|---|---|")
    for name, stats in pools.items():
        lines.append(
            f"| {name} | {stats['total']} | {stats['any_repeat_pct']}% | "
            f"{stats['adjacent_word_pct']}% | {stats['vowel_apart_word_pct']}% |"
        )
    lines.append("")

    lines.append("## Distinct letters in the word (5 = no repeat)")
    lines.append("| pool | " + " | ".join(["5", "4", "3", "2"]) + " |")
    lines.append("|" + "---|" * 5)
    for name, stats in pools.items():
        cells = [f"{stats['distinct_pct'].get(k, 0.0)}%" for k in ("5", "4", "3", "2")]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Repeat letter class: adjacent vs non-adjacent")
    lines.append(
        "Each repeated letter counted once per word. 'adjacent' is the share of that "
        "class whose copies touch; baseline is the class share of all letters in the pool."
    )
    lines.append("")
    lines.append("| pool | kind | repeat instances | adjacent | baseline |")
    lines.append("|---|---|---|---|---|")
    for name, stats in pools.items():
        for kind in ("consonant", "vowel", "y"):
            n = stats["repeat_instances"].get(kind, 0)
            touching = stats["adjacent_instances"].get(kind, 0)
            touching_pct = round(100 * touching / n, 1) if n else 0.0
            lines.append(
                f"| {name} | {kind} | {n} ({stats['repeat_instance_pct'].get(kind, 0.0)}%) | "
                f"{touching_pct}% | "
                f"{stats['baseline_letter_pct'].get(kind, 0.0)}% |"
            )
    lines.append("")

    lines.append("## Over-representation among repeats (vs letter baseline)")
    lines.append("| pool | vowel | consonant | y |")
    lines.append("|---|---|---|---|")
    for name, stats in pools.items():
        cells = []
        for kind in ("vowel", "consonant", "y"):
            share = stats["repeat_instance_pct"].get(kind, 0.0)
            baseline = stats["baseline_letter_pct"].get(kind, 0.0)
            cells.append(f"{ratio(share, baseline)}x ({share}% vs {baseline}%)")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Commonest repeated letters (adjacent or not)")
    for name, stats in pools.items():
        top = ", ".join(
            f"{ch.upper()} {n}" for ch, n in stats["top_repeated_letters"][:8]
        )
        lines.append(f"- {name}: {top}")
    lines.append("")

    lines.append("## Rare shapes (answers pool)")
    answers = pools["answers"]
    lines.append(
        f"- Three or more copies of one letter: {answers['triple_plus']} "
        f"({round(100 * answers['triple_plus'] / answers['total'], 2)}%)"
    )
    lines.append(
        f"- Two independent pairs: {answers['two_pairs']} "
        f"({round(100 * answers['two_pairs'] / answers['total'], 1)}%)"
    )
    lines.append(
        f"- Repeated Y: {len(answers['y_repeat_words'])} - "
        + ", ".join(answers["y_repeat_words"])
    )
    lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    allowed = load_words(ALLOWED_PATH)
    pools = {
        "answers": pool_stats(answers),
        "allowed-only": pool_stats(allowed),
        "all valid": pool_stats(sorted(set(answers) | set(allowed))),
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "duplicates.json").write_text(json.dumps(pools, indent=2))
    write_markdown(pools, RESULTS_DIR / "duplicates.md")
    for name, stats in pools.items():
        print(
            f"{name}: {stats['any_repeat_pct']}% repeat a letter, "
            f"{stats['adjacent_word_pct']}% have an adjacent double"
        )
    print("Wrote results/duplicates.json and results/duplicates.md")


if __name__ == "__main__":
    main()
