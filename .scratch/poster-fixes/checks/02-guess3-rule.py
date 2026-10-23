#!/usr/bin/env python3
"""Ticket 01/02/03/10 agreement check: sections I-IV share one source.

Sections III (hit-count reference) and IV (per-pattern cards) of
infographic-v4.html must reproduce the strategy labels and guess-3 words in
results/hit_tree.json, and the rule printed in section III must be true of
every burn/split word shown: a burn word carries no hit letter, a split word
reuses one.

Sections I (method flow) and II (play tree) must name no guess word. Instead
each hit-count band carries its games-weighted action mix, ~Left (mean pool
size) and ~After (mean expected candidates left), which this check recomputes
from data/answers.txt.

Run: python3 .scratch/poster-fixes/checks/02-guess3-rule.py
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POSTER_PATH = ROOT / "infographic-v4.html"
HIT_TREE_JSON = ROOT / "results" / "hit_tree.json"
ANSWERS_PATH = ROOT / "data" / "answers.txt"
PAIR = ("soare", "clint")
ACTION_ORDER = ["Candidate", "Split word", "Burn word"]
# Guess words the poster used to name one per band; none may survive.
BANNED_WORDS = ["dumpy", "debug", "reedy", "gawky", "match", "resin"]
MIX_RE = re.compile(
    r"(Candidate|Split(?: word)?|Burn(?: word)?)\s+(\d+)%", re.IGNORECASE
)
MIX_NAMES = {
    "candidate": "Candidate",
    "split": "Split word",
    "split word": "Split word",
    "burn": "Burn word",
    "burn word": "Burn word",
}


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def as_int(text: str) -> int:
    return int(re.sub(r"[^0-9-]", "", text))


def as_float(text: str) -> float:
    return float(re.sub(r"[^0-9.]", "", text))


def get_section(html: str, anchor_id: str) -> str:
    at = html.index(f'id="{anchor_id}"')
    start = html.rindex("<section", 0, at)
    return html[start : html.index("</section>", start)]


def parse_table(chunk: str) -> list[list[str]]:
    table = re.search(r"<table[^>]*>.*?</table>", chunk, re.DOTALL)
    assert table, "no table in chunk"
    tbody = re.search(r"<tbody>(.*?)</tbody>", table.group(0), re.DOTALL)
    assert tbody, "table has no tbody"
    return [
        [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)]
        for tr in re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.DOTALL)
    ]


def parse_cards(section: str) -> list[dict]:
    cards = []
    for chunk in section.split('<div class="pat-card">')[1:]:
        heading = re.search(r"<h3>(.*?)</h3>", chunk, re.DOTALL)
        sub = re.search(r'<p class="pat-sub">(.*?)</p>', chunk, re.DOTALL)
        note = re.search(r'<p class="chart-note"[^>]*>(.*?)</p>', chunk, re.DOTALL)
        cards.append(
            {
                "heading": clean(heading.group(1)) if heading else "",
                "sub": clean(sub.group(1)) if sub else "",
                "rows": parse_table(chunk),
                "note": clean(note.group(1)) if note else "",
            }
        )
    return cards


def hit_letters(pair_patterns: tuple[str, str]) -> set[str]:
    letters = set()
    for guess, pattern in zip(PAIR, pair_patterns):
        for i, ch in enumerate(pattern):
            if ch != "X":
                letters.add(guess[i])
    return letters


def flow_field(chunk: str, name: str) -> str:
    match = re.search(rf'<div class="flow-{name}">(.*?)</div>', chunk, re.DOTALL)
    return clean(match.group(1)) if match else ""


def parse_flow(section: str) -> list[dict]:
    steps = []
    for chunk in section.split('<div class="flow-step">')[1:]:
        note = re.search(r'<p class="flow-note">(.*?)</p>', chunk, re.DOTALL)
        steps.append(
            {
                "num": flow_field(chunk, "num"),
                "strat": flow_field(chunk, "strat"),
                "ex": flow_field(chunk, "ex"),
                "share": flow_field(chunk, "share"),
                "note": clean(note.group(1)) if note else "",
            }
        )
    return steps


# --- independent recomputation of every hit-count band ---------------------


def feedback(guess: str, answer: str) -> str:
    """Standard Wordle feedback (greens first, then yellows left to right)."""
    result = ["X"] * 5
    remaining: dict[str, int] = defaultdict(int)
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = "G"
        else:
            remaining[answer[i]] += 1
    for i in range(5):
        if result[i] == "G":
            continue
        if remaining[guess[i]] > 0:
            result[i] = "Y"
            remaining[guess[i]] -= 1
    return "".join(result)


def sum_sq(guess: str, pool: list[str]) -> int:
    counts: dict[str, int] = defaultdict(int)
    for answer in pool:
        counts[feedback(guess, answer)] += 1
    return sum(size * size for size in counts.values())


def choose_word(answers: list[str], pool: list[str]) -> tuple[str, int, bool]:
    in_pool = set(pool)
    best_key = None
    best_word = None
    best_sq = None
    for word in answers:
        sq = sum_sq(word, pool)
        key = (sq, 0 if word in in_pool else 1, word)
        if best_key is None or key < best_key:
            best_key, best_word, best_sq = key, word, sq
    assert best_word is not None and best_sq is not None
    return best_word, best_sq, best_word in in_pool


def label(word: str, in_pool: bool, letters: set[str]) -> str:
    if in_pool:
        return "Candidate"
    return "Split word" if set(word) & letters else "Burn word"


def half_up(value: float) -> int:
    return int(value + 0.5)


def recompute_bands(answers: list[str]) -> dict[int, dict]:
    buckets: dict[int, dict[tuple[str, str], list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for answer in answers:
        key = (feedback(PAIR[0], answer), feedback(PAIR[1], answer))
        buckets[len(hit_letters(key))][key].append(answer)

    bands: dict[int, dict] = {}
    for hits, patterns in buckets.items():
        games = sum(len(pool) for pool in patterns.values())
        pool_total = 0
        after_total = 0
        mix: dict[str, int] = defaultdict(int)
        for pair, pool in patterns.items():
            n = len(pool)
            pool_total += n * n
            word, sq, in_pool = choose_word(answers, pool)
            after_total += sq
            mix[label(word, in_pool, hit_letters(pair))] += n
        bands[hits] = {
            "games": games,
            "share": round(100 * games / len(answers), 1),
            "left": pool_total / games,
            "after": after_total / games,
            "mix": {
                action: half_up(100 * mix[action] / games)
                for action in ACTION_ORDER
                if mix[action]
            },
        }
    return bands


def parse_mix(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for match in MIX_RE.finditer(text):
        out[MIX_NAMES[match.group(1).lower()]] = int(match.group(2))
    return out


def mix_error(text: str, want: dict[str, int]) -> str:
    """Return '' if the Strategy cell states the recomputed mix, else why not."""
    if re.search(r"\balways\b", text, re.IGNORECASE):
        if len(want) != 1:
            return f"{text!r} says 'always' but the mix is {want}"
        action, pct = next(iter(want.items()))
        if pct != 100:
            return f"{text!r} says 'always' but {action} is only {pct}%"
        if action.split()[0].lower() not in text.lower():
            return f"{text!r} does not name {action}"
        return ""
    got = parse_mix(text)
    if got != want:
        return f"{text!r} -> {got} != {want}"
    return ""


def main() -> int:
    failures: list[str] = []
    rows = json.loads(HIT_TREE_JSON.read_text())
    html = POSTER_PATH.read_text()
    reference = get_section(html, "reference")
    answers = [
        line.strip().lower()
        for line in ANSWERS_PATH.read_text().splitlines()
        if line.strip()
    ]
    bands = recompute_bands(answers)
    overall_left = (
        sum(band["games"] * band["left"] for band in bands.values()) / len(answers)
    )

    # Sections I and II carry a strategy, never a guess word.
    method_section = get_section(html, "method")
    tree_section = get_section(html, "tree")
    if round(overall_left, 2) != 4.37:
        failures.append(
            f"games-weighted ~Left across bands is {overall_left:.2f}, expected 4.37"
        )
    if "4.37" not in clean(method_section):
        failures.append("section I does not state the 4.37 candidates-left headline")
    banned_text = clean(method_section + " " + tree_section)
    for word in BANNED_WORDS:
        if re.search(rf"\b{word}\b", banned_text, re.IGNORECASE):
            failures.append(f"sections I/II still name the guess word {word.upper()}")
    if 'class="g3"' in tree_section:
        failures.append("section II still has a guess-word column")

    # Section II: Hits | Share | ~Left | Strategy | ~After, recomputed.
    tree_rows = parse_table(tree_section)
    if len(tree_rows) != len(bands):
        failures.append(f"section II has {len(tree_rows)} rows, expected {len(bands)}")
    tree_strategy: dict[int, str] = {}
    for hits, cells in zip(sorted(bands), tree_rows):
        want = bands[hits]
        if len(cells) != 5:
            failures.append(f"section II {hits} hits: {len(cells)} cells, expected 5")
            continue
        got_hits, got_share, got_left, got_strategy, got_after = cells
        tree_strategy[hits] = got_strategy
        if as_int(got_hits) != hits:
            failures.append(f"section II row {hits}: hit label {got_hits}")
        if as_float(got_share) != want["share"]:
            failures.append(f"section II {hits}: share {got_share} != {want['share']}%")
        if as_float(got_left) != round(want["left"], 1):
            failures.append(
                f"section II {hits}: ~Left {got_left} != {round(want['left'], 1)}"
            )
        if as_float(got_after) != round(want["after"], 2):
            failures.append(
                f"section II {hits}: ~After {got_after} != {round(want['after'], 2)}"
            )
        problem = mix_error(got_strategy, want["mix"])
        if problem:
            failures.append(f"section II {hits}: strategy {problem}")

    # Section I is a summary band; it must agree with section II and never
    # name a guess word.
    flow = parse_flow(method_section)
    if len(flow) != len(bands):
        failures.append(f"section I has {len(flow)} bands, expected {len(bands)}")
    for hits, step in zip(sorted(bands), flow):
        want = bands[hits]
        if as_int(step["num"]) != hits:
            failures.append(f"section I band {step['num']} != hit count {hits}")
        if step["ex"]:
            failures.append(f"section I {hits}: still shows the word {step['ex']}")
        problem = mix_error(step["strat"], want["mix"])
        if problem:
            failures.append(f"section I {hits}: strategy {problem}")
        if hits in tree_strategy and parse_mix(step["strat"]) != parse_mix(
            tree_strategy[hits]
        ):
            failures.append(
                f"section I {hits}: mix {step['strat']!r} disagrees with "
                f"section II {tree_strategy[hits]!r}"
            )
        pct = re.search(r"([\d.]+)%", step["share"])
        left = re.search(r"~\s*([\d.]+)", step["share"])
        if not pct or not left:
            failures.append(f"section I {hits}: share line {step['share']!r}")
        else:
            if float(pct.group(1)) != want["share"]:
                failures.append(
                    f"section I {hits}: share {pct.group(1)}% != {want['share']}%"
                )
            if float(left.group(1)) != round(want["left"], 1):
                failures.append(
                    f"section I {hits}: ~{left.group(1)} left != "
                    f"{round(want['left'], 1)}"
                )
        if hits == 5 and not re.search(r"anagram|tie", step["note"], re.IGNORECASE):
            failures.append("section I five-hit band lost its anagram-tie caveat")

    # Section III keeps its per-pattern counts and top-pool action sets.
    ref_rows = parse_table(reference)
    if len(ref_rows) != len(rows):
        failures.append(f"section III has {len(ref_rows)} rows, expected {len(rows)}")
    for row, cells in zip(rows, ref_rows):
        if len(cells) != 6:
            failures.append(f"section III {row['hits']} hits: {len(cells)} cells")
            continue
        got_hits, got_share, got_patterns, got_avg, got_max, got_actions = cells
        if as_int(got_hits) != row["hits"]:
            failures.append(f"section III row {row['hits']}: hit label {got_hits}")
        if as_float(got_share) != row["share_pct"]:
            failures.append(f"section III {row['hits']}: share {got_share}")
        if as_int(got_patterns) != row["patterns"]:
            failures.append(f"section III {row['hits']}: patterns {got_patterns}")
        if as_float(got_avg) != row["avg_candidates"]:
            failures.append(f"section III {row['hits']}: avg {got_avg}")
        if as_int(got_max) != row["max_candidates"]:
            failures.append(f"section III {row['hits']}: max {got_max}")
        shown = {a.strip() for a in got_actions.split("·")[0].split(",") if a.strip()}
        if shown != set(row["actions"]):
            failures.append(
                f"section III {row['hits']}: actions {shown} != {set(row['actions'])}"
            )
        if row["hits"] == 5 and not re.search(r"anagram|tie", got_actions, re.IGNORECASE):
            failures.append("section III five-hit row lost its anagram-tie caveat")

    # Section IV keeps its per-pattern cards.
    cards = parse_cards(get_section(html, "patterns"))
    if len(cards) != len(rows):
        failures.append(f"section IV has {len(cards)} cards, expected {len(rows)}")
    for row, card in zip(rows, cards):
        if not card["heading"].startswith(f"{row['hits']} hit"):
            failures.append(
                f"section IV card order: {card['heading']!r} for {row['hits']} hits"
            )
        if re.search(
            r"\b(Candidate|Split(?: word)?|Burn(?: word)?)\b", card["heading"]
        ):
            failures.append(
                f"section IV {row['hits']} hits: title still names an action: "
                f"{card['heading']!r}"
            )
        if "largest" not in card["sub"].lower():
            failures.append(
                f"section IV {row['hits']} hits: subtitle does not say the rows are "
                f"the band's largest pools: {card['sub']!r}"
            )
        pool_claim = re.search(rf"(\d+)\s+of\s+{row['patterns']}\b", card["sub"])
        if not pool_claim:
            failures.append(
                f"section IV {row['hits']} hits: subtitle does not state how many "
                f"of the band's {row['patterns']} pools are shown: {card['sub']!r}"
            )
        elif int(pool_claim.group(1)) != len(card["rows"]):
            failures.append(
                f"section IV {row['hits']} hits: subtitle claims {pool_claim.group(1)} "
                f"of {row['patterns']} pools but {len(card['rows'])} rows are shown"
            )
        if len(card["rows"]) != len(row["top_patterns"]):
            failures.append(
                f"section IV {row['hits']} hits: {len(card['rows'])} rows, "
                f"expected {len(row['top_patterns'])}"
            )
            continue
        for cells, top in zip(card["rows"], row["top_patterns"]):
            if len(cells) != 6:
                failures.append(f"section IV {row['hits']} hits: {len(cells)} cells")
                continue
            got_g1, got_g2, got_count, got_action, got_word, got_left = cells
            label_text = f"{top['g1_pattern']}/{top['g2_pattern']}"
            if (got_g1, got_g2) != (top["g1_pattern"], top["g2_pattern"]):
                failures.append(
                    f"section IV {row['hits']}: patterns {got_g1}/{got_g2} "
                    f"!= {top['g1_pattern']}/{top['g2_pattern']}"
                )
            if as_int(got_count) != top["candidates"]:
                failures.append(
                    f"section IV {label_text}: count {got_count} != {top['candidates']}"
                )
            if got_action != top["action"]:
                failures.append(
                    f"section IV {label_text}: action {got_action!r} != {top['action']!r}"
                )
            if got_word.lower() != top["guess3"]:
                failures.append(
                    f"section IV {label_text}: word {got_word} != {top['guess3'].upper()}"
                )
            if as_float(got_left) != top["expected_remaining"]:
                failures.append(
                    f"section IV {label_text}: left {got_left} "
                    f"!= {top['expected_remaining']}"
                )
        if row["hits"] == 5 and not re.search(r"anagram|tie", card["note"], re.IGNORECASE):
            failures.append("section IV five-hit card lost its anagram-tie caveat")

    # The printed rule must match hit_tree.json and describe what the labels do.
    rule = rows[0]["rule"]
    if clean(rule) not in clean(reference):
        failures.append("section III does not print the hit_tree.json rule verbatim")
    if "fresh" in rule.lower():
        failures.append("rule still claims a burn word tests only fresh letters")
    for row in rows:
        for top in row["top_patterns"]:
            letters = hit_letters((top["g1_pattern"], top["g2_pattern"]))
            reuses = bool(set(top["guess3"]) & letters)
            if top["action"] == "Burn word" and reuses:
                failures.append(
                    f"{top['guess3'].upper()} is labelled Burn word but reuses "
                    "a hit letter"
                )
            if top["action"] == "Split word" and not reuses:
                failures.append(
                    f"{top['guess3'].upper()} is labelled Split word but reuses "
                    "no hit letter"
                )

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS")
    print("  sections I/II name no guess word; mixes, shares, ~Left and ~After recompute")
    print("  section III counts and action sets match hit_tree.json")
    print("  section IV pattern rows match hit_tree.json")
    print("  rule printed in section III is true of every burn/split word")
    return 0


if __name__ == "__main__":
    sys.exit(main())
