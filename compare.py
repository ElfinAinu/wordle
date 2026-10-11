# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Score hand-picked disjoint opener pairs side by side."""

from analyze import ANSWERS_PATH, encode, letter_counts, load_words
from coverage import letter_masks, score_pair

PAIRS = [
    ("salon", "trice"),
    ("crise", "talon"),
    ("scone", "trail"),
    ("soare", "clint"),
]


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    answer_codes = encode(answers)
    answer_counts = letter_counts(answer_codes)
    masks = letter_masks(answers)
    distinct_counts = masks.sum(axis=1)

    print(f"{'pair':16} {'remaining':>9} {'solved2%':>9} {'spot%':>6}")
    for first, second in PAIRS:
        row = score_pair(
            first, second, answer_codes, answer_counts, masks, distinct_counts
        )
        print(
            f"{first.upper() + ' + ' + second.upper():16} "
            f"{row['expected_remaining']:9.2f} {row['solved_on_two_pct']:9.2f} {row['spot_rate_pct']:6.1f}"
        )


if __name__ == "__main__":
    main()
