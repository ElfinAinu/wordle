# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Analyze the Wordle answer list for the performance poster.

Outputs results/analysis.json (machine) and results/analysis.md (human).
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
ANSWERS_PATH = ROOT / "data" / "answers.txt"
ALLOWED_PATH = ROOT / "data" / "allowed.txt"
RESULTS_DIR = ROOT / "results"

VOWELS = set("aeiou")
POSITIONS = 5
ALPHABET = 26
NOTABLE_OPENERS = [
    "salet",
    "trace",
    "crate",
    "slate",
    "crane",
    "audio",
    "stare",
    "raise",
    "adieu",
    "louie",
]


def load_words(path: Path) -> list[str]:
    return [
        line.strip().lower() for line in path.read_text().splitlines() if line.strip()
    ]


def encode(words: list[str]) -> np.ndarray:
    return np.array([[ord(ch) - 97 for ch in word] for word in words], dtype=np.int8)


def letter_counts(codes: np.ndarray) -> np.ndarray:
    counts = np.zeros((codes.shape[0], ALPHABET), dtype=np.int16)
    for position in range(codes.shape[1]):
        counts[np.arange(codes.shape[0]), codes[:, position]] += 1
    return counts


def pattern_codes(
    guess: np.ndarray, answer_codes: np.ndarray, answers_letter_counts: np.ndarray
) -> np.ndarray:
    """Return the feedback pattern (base-3 code per answer) for one guess."""
    green = answer_codes == guess
    state = np.where(green, 2, 0).astype(np.int8)
    green_matches_per_letter = np.zeros(
        (answer_codes.shape[0], ALPHABET), dtype=np.int8
    )
    for position in range(POSITIONS):
        letter = guess[position]
        green_matches_per_letter[green[:, position], letter] += 1
    for position in range(POSITIONS):
        letter = guess[position]
        yellow = (~green[:, position]) & (
            answers_letter_counts[:, letter] > green_matches_per_letter[:, letter]
        )
        state[yellow, position] = 1
    return state @ (3 ** np.arange(POSITIONS))


def score_guess(
    guess: np.ndarray, answer_codes: np.ndarray, answers_letter_counts: np.ndarray
) -> tuple[float, float]:
    """Return (entropy in bits, expected remaining candidates) for one guess."""
    patterns = pattern_codes(guess, answer_codes, answers_letter_counts)
    _, counts = np.unique(patterns, return_counts=True)
    total = counts.sum()
    probability = counts / total
    entropy = float(-(probability * np.log2(probability)).sum())
    expected_remaining = float((counts.astype(np.float64) ** 2).sum() / total)
    return entropy, expected_remaining


def rank_openers(guess_words: list[str], answer_words: list[str], top_n: int) -> dict:
    answer_codes = encode(answer_words)
    answers_letter_counts = letter_counts(answer_codes)
    guess_codes = encode(guess_words)

    scores = []
    for index in range(len(guess_words)):
        entropy, expected_remaining = score_guess(
            guess_codes[index], answer_codes, answers_letter_counts
        )
        scores.append((guess_words[index], entropy, expected_remaining))

    scores.sort(key=lambda row: (-row[1], row[2]))
    notable = {word: None for word in NOTABLE_OPENERS if word in set(guess_words)}
    for rank, (word, entropy, expected_remaining) in enumerate(scores, start=1):
        if word in notable:
            notable[word] = {
                "rank": rank,
                "entropy": entropy,
                "expected_remaining": expected_remaining,
            }

    return {
        "top": [
            {"word": w, "entropy": e, "expected_remaining": r}
            for w, e, r in scores[:top_n]
        ],
        "notable": notable,
    }


def letter_stats(answer_words: list[str]) -> dict:
    total = len(answer_words)
    overall = Counter()
    by_position = [Counter() for _ in range(POSITIONS)]
    first_letters = Counter()
    last_letters = Counter()
    last_bigrams = Counter()
    vowel_counts = Counter()
    doubles = 0
    repeats = 0

    for word in answer_words:
        overall.update(set(word))
        for position, letter in enumerate(word):
            by_position[position][letter] += 1
        first_letters[word[0]] += 1
        last_letters[word[-1]] += 1
        last_bigrams[word[-2:]] += 1
        vowel_counts[sum(1 for ch in word if ch in VOWELS)] += 1
        if any(word[i] == word[i + 1] for i in range(POSITIONS - 1)):
            doubles += 1
        if len(set(word)) < POSITIONS:
            repeats += 1

    return {
        "total_answers": total,
        "overall_contain_pct": {
            letter: round(100 * count / total, 1)
            for letter, count in overall.most_common()
        },
        "by_position_top": [
            {
                letter: round(100 * count / total, 1)
                for letter, count in counter.most_common(6)
            }
            for counter in by_position
        ],
        "first_letter_pct": {
            letter: round(100 * count / total, 1)
            for letter, count in first_letters.most_common()
        },
        "last_letter_pct": {
            letter: round(100 * count / total, 1)
            for letter, count in last_letters.most_common()
        },
        "last_bigram_top": {
            bg: round(100 * count / total, 1)
            for bg, count in last_bigrams.most_common(12)
        },
        "vowel_count_pct": {
            str(k): round(100 * v / total, 1) for k, v in sorted(vowel_counts.items())
        },
        "repeat_letter_pct": round(100 * repeats / total, 1),
        "adjacent_double_pct": round(100 * doubles / total, 1),
    }


def write_markdown(stats: dict, openers: dict, path: Path) -> None:
    lines = ["# Wordle answer-list analysis", ""]
    lines.append(f"Answers analyzed: **{stats['total_answers']}**")
    lines.append("")

    lines.append("## Letter frequency (share of answers containing letter)")
    top_overall = list(stats["overall_contain_pct"].items())[:10]
    lines.append("| " + " | ".join(letter.upper() for letter, _ in top_overall) + " |")
    lines.append("|" + "---|" * len(top_overall))
    lines.append("| " + " | ".join(f"{pct}%" for _, pct in top_overall) + " |")
    lines.append("")

    lines.append("## Top letters by position")
    for position, counter in enumerate(stats["by_position_top"], start=1):
        top = ", ".join(
            f"{letter.upper()} {pct}%" for letter, pct in list(counter.items())[:5]
        )
        lines.append(f"{position}. {top}")
    lines.append("")

    lines.append("## Endings")
    last = ", ".join(
        f"{letter.upper()} {pct}%"
        for letter, pct in list(stats["last_letter_pct"].items())[:6]
    )
    lines.append(f"Last letter: {last}")
    bigrams = ", ".join(
        f"{bg.upper()} {pct}%" for bg, pct in list(stats["last_bigram_top"].items())[:8]
    )
    lines.append(f"Last two letters: {bigrams}")
    lines.append("")

    lines.append("## Word shape")
    vowels = ", ".join(
        f"{count} vowels: {pct}%" for count, pct in stats["vowel_count_pct"].items()
    )
    lines.append(f"{vowels}")
    lines.append(
        f"Repeats a letter: {stats['repeat_letter_pct']}% "
        f"(adjacent double: {stats['adjacent_double_pct']}%)"
    )
    lines.append("")

    lines.append("## Opener ranking (entropy over all answers)")
    lines.append("| Rank | Word | Entropy (bits) | Expected remaining |")
    lines.append("|---|---|---|---|")
    for rank, row in enumerate(openers["top"], start=1):
        lines.append(
            f"| {rank} | {row['word'].upper()} | {row['entropy']:.3f} | {row['expected_remaining']:.2f} |"
        )
    lines.append("")

    lines.append("## Notable openers")
    lines.append("| Word | Rank | Entropy (bits) | Expected remaining |")
    lines.append("|---|---|---|---|")
    for word, row in sorted(
        openers["notable"].items(), key=lambda item: item[1]["rank"]
    ):
        lines.append(
            f"| {word.upper()} | {row['rank']} | {row['entropy']:.3f} | {row['expected_remaining']:.2f} |"
        )
    lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    allowed = load_words(ALLOWED_PATH)
    guess_pool = sorted(set(answers) | set(allowed))

    stats = letter_stats(answers)
    openers = rank_openers(guess_pool, answers, top_n=25)

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "analysis.json").write_text(
        json.dumps({"letters": stats, "openers": openers}, indent=2)
    )
    write_markdown(stats, openers, RESULTS_DIR / "analysis.md")
    print(
        f"Best opener: {openers['top'][0]['word'].upper()} "
        f"({openers['top'][0]['entropy']:.3f} bits)"
    )
    print("Wrote results/analysis.json and results/analysis.md")


if __name__ == "__main__":
    main()
