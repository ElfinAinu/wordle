# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Optimal guess 3 after SOARE + CLINT return all gray.

All-gray on both means the answer avoids all 10 tested letters, so the
candidate set collapses to answers built from the remaining 16 letters.
Ranks guess-3 options by entropy over that set and shows its positional
letter frequencies.
"""

from analyze import (
    ALLOWED_PATH,
    ANSWERS_PATH,
    encode,
    letter_counts,
    load_words,
    score_guess,
)

BURNED = set("soareclint")


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    allowed = load_words(ALLOWED_PATH)
    pool = sorted(set(answers) | set(allowed))

    candidates = [word for word in answers if not set(word) & BURNED]
    print(f"candidates after all-gray SOARE+CLINT: {len(candidates)}")
    print(" ", " ".join(candidates))

    codes = encode(candidates)
    counts = letter_counts(codes)
    print("\npositional frequency within candidates (% of candidates):")
    for position in range(5):
        freq = {}
        for word in candidates:
            freq[word[position]] = freq.get(word[position], 0) + 1
        top = sorted(freq.items(), key=lambda kv: -kv[1])[:6]
        print(
            f"  pos {position + 1}: "
            + ", ".join(
                f"{ch.upper()} {100 * n / len(candidates):.0f}%" for ch, n in top
            )
        )

    ranked = []
    for word in pool:
        entropy, expected = score_guess(encode([word])[0], codes, counts)
        ranked.append((word, entropy, expected))
    ranked.sort(key=lambda row: (-row[1], row[2]))

    print("\nbest guess 3 (entropy over remaining candidates):")
    for word, entropy, expected in ranked[:10]:
        tag = "  <- candidate" if word in candidates else ""
        print(
            f"  {word.upper():6} entropy {entropy:.3f}  expected left {expected:.2f}{tag}"
        )


if __name__ == "__main__":
    main()
