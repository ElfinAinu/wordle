# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "matplotlib"]
# ///
"""Loose draft heatmap of the Wordle answer list, shaped like a word grid.

Rows: letters sorted by overall frequency (most common on top).
Columns: the five positions of a guess, like a Wordle row.
Cells: % of answers with that letter in that position.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
ANSWERS_PATH = ROOT / "data" / "answers.txt"
DRAFT_DIR = ROOT / "results" / "draft"

LETTERS = "abcdefghijklmnopqrstuvwxyz"
INDEX = {ch: i for i, ch in enumerate(LETTERS)}
POSITIONS = 5


def load_answers() -> list[str]:
    return [
        line.strip().lower()
        for line in ANSWERS_PATH.read_text().splitlines()
        if line.strip()
    ]


def position_matrix(answers: list[str]) -> np.ndarray:
    counts = np.zeros((26, POSITIONS))
    for word in answers:
        for position, ch in enumerate(word):
            counts[INDEX[ch], position] += 1
    return 100 * counts / len(answers)


def frequency_tables(answers: list[str]) -> tuple[list[str], np.ndarray]:
    overall = np.zeros(26)
    for word in answers:
        for ch in set(word):
            overall[INDEX[ch]] += 1
    order = np.argsort(-overall)
    return [LETTERS[i] for i in order], position_matrix(answers)[order]


def draw_word_grid(
    letters: list[str],
    by_position: np.ndarray,
    total: int,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(4.2, 0.24 * len(letters) + 1.2))
    ax.imshow(by_position, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(
        range(POSITIONS), [f"pos {i}" for i in range(1, POSITIONS + 1)], fontsize=9
    )
    ax.set_yticks(range(len(letters)), [ch.upper() for ch in letters], fontsize=9)
    ax.set_title(
        f"DRAFT — letter x position, % of {total} answers (color only)", fontsize=9
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path}")


def draw_pair_grids(
    pairs: list[tuple[str, str]], matrix: np.ndarray, path: Path
) -> None:
    fig, axes = plt.subplots(
        len(pairs), 1, figsize=(6.0, 1.35 * len(pairs) + 0.9), squeeze=False
    )
    threshold = matrix.max() / 2
    for row, (first, second) in enumerate(pairs):
        ax = axes[row][0]
        values = np.array(
            [
                [matrix[INDEX[ch], pos] for pos, ch in enumerate(word)]
                for word in (first, second)
            ]
        )
        ax.imshow(values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=matrix.max())
        for line, word in enumerate((first, second)):
            for pos, ch in enumerate(word):
                ax.text(
                    pos,
                    line,
                    ch.upper(),
                    ha="center",
                    va="center",
                    fontsize=14,
                    fontweight="bold",
                    color="white" if matrix[INDEX[ch], pos] > threshold else "black",
                )
        ax.set_yticks([])
        ax.set_xticks(
            range(POSITIONS),
            [f"pos {i}" for i in range(1, POSITIONS + 1)]
            if row == len(pairs) - 1
            else [],
            fontsize=9,
        )
        ax.set_title(f"{first.upper()} + {second.upper()}", fontsize=11)
    fig.suptitle(
        "DRAFT — disjoint opener pairs; color = letter frequency at position",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path}")


def main() -> None:
    answers = load_answers()
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    letters, by_position = frequency_tables(answers)
    draw_word_grid(letters, by_position, len(answers), DRAFT_DIR / "word_grid.png")
    draw_pair_grids(
        [
            ("salon", "trice"),
            ("crise", "talon"),
            ("scone", "trail"),
            ("soare", "clint"),
        ],
        position_matrix(answers),
        DRAFT_DIR / "pair_grids.png",
    )


if __name__ == "__main__":
    main()
