#!/usr/bin/env python3
"""Ticket 01/02/03 agreement check: sections I-IV share one source.

Sections I (method flow), II (play tree), III (hit-count reference) and IV
(per-pattern cards) of infographic-v4.html must reproduce the strategy labels
and guess-3 words in results/hit_tree.json. The rule printed in section III
must also be true of every burn/split word shown: a burn word carries no hit
letter, a split word reuses one.

Run: python3 .scratch/poster-fixes/checks/02-guess3-rule.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POSTER_PATH = ROOT / "infographic-v4.html"
HIT_TREE_JSON = ROOT / "results" / "hit_tree.json"
PAIR = ("soare", "clint")
ACTION_ORDER = ["Candidate", "Split word", "Burn word"]


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
        note = re.search(r'<p class="chart-note"[^>]*>(.*?)</p>', chunk, re.DOTALL)
        cards.append(
            {
                "heading": clean(heading.group(1)) if heading else "",
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


def band_hits(text: str) -> list[int]:
    parts = [as_int(part) for part in re.split(r"[–—\-]", clean(text)) if part]
    if len(parts) == 2:
        return list(range(parts[0], parts[1] + 1))
    return parts


def main() -> int:
    failures: list[str] = []
    rows = json.loads(HIT_TREE_JSON.read_text())
    html = POSTER_PATH.read_text()
    reference = get_section(html, "reference")

    tree_rows = parse_table(get_section(html, "tree"))
    if len(tree_rows) != len(rows):
        failures.append(f"section II has {len(tree_rows)} rows, expected {len(rows)}")
    for row, cells in zip(rows, tree_rows):
        if len(cells) != 6:
            failures.append(f"section II {row['hits']} hits: {len(cells)} cells")
            continue
        top = row["top_patterns"][0]
        got_hits, got_share, got_left, got_strategy, got_word, got_after = cells
        if as_int(got_hits) != row["hits"]:
            failures.append(f"section II row {row['hits']}: hit label {got_hits}")
        if as_float(got_share) != row["share_pct"]:
            failures.append(f"section II {row['hits']}: share {got_share}")
        if as_float(got_left) != row["avg_candidates"]:
            failures.append(f"section II {row['hits']}: avg {got_left}")
        if got_strategy != row["strategy"]:
            failures.append(
                f"section II {row['hits']}: strategy {got_strategy!r} "
                f"!= {row['strategy']!r}"
            )
        if got_word.lower() != top["guess3"]:
            failures.append(
                f"section II {row['hits']}: guess 3 {got_word} "
                f"!= {top['guess3'].upper()}"
            )
        if as_float(got_after) != top["expected_remaining"]:
            failures.append(
                f"section II {row['hits']}: after {got_after} "
                f"!= {top['expected_remaining']}"
            )

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

    cards = parse_cards(get_section(html, "patterns"))
    if len(cards) != len(rows):
        failures.append(f"section IV has {len(cards)} cards, expected {len(rows)}")
    for row, card in zip(rows, cards):
        if not card["heading"].startswith(f"{row['hits']} hit"):
            failures.append(
                f"section IV card order: {card['heading']!r} for {row['hits']} hits"
            )
        heading_actions = card["heading"].split("—")[-1].strip()
        shown = {a.strip() for a in heading_actions.split(",") if a.strip()}
        if shown != set(row["actions"]):
            failures.append(
                f"section IV {row['hits']} hits: heading actions {shown} "
                f"!= {set(row['actions'])}"
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
            label = f"{top['g1_pattern']}/{top['g2_pattern']}"
            if (got_g1, got_g2) != (top["g1_pattern"], top["g2_pattern"]):
                failures.append(
                    f"section IV {row['hits']}: patterns {got_g1}/{got_g2} "
                    f"!= {top['g1_pattern']}/{top['g2_pattern']}"
                )
            if as_int(got_count) != top["candidates"]:
                failures.append(
                    f"section IV {label}: count {got_count} != {top['candidates']}"
                )
            if got_action != top["action"]:
                failures.append(
                    f"section IV {label}: action {got_action!r} != {top['action']!r}"
                )
            if got_word.lower() != top["guess3"]:
                failures.append(
                    f"section IV {label}: word {got_word} != {top['guess3'].upper()}"
                )
            if as_float(got_left) != top["expected_remaining"]:
                failures.append(
                    f"section IV {label}: left {got_left} "
                    f"!= {top['expected_remaining']}"
                )
        if row["hits"] == 5 and not re.search(r"anagram|tie", card["note"], re.IGNORECASE):
            failures.append("section IV five-hit card lost its anagram-tie caveat")

    # Section I (method flow) is a summary band; every band it keeps must be
    # true of every hit count inside it, with labels and words from hit_tree.json.
    flow = parse_flow(get_section(html, "method"))
    if not flow:
        failures.append("section I has no flow bands")
    bands = [band_hits(step["num"]) for step in flow]
    covered = [h for band in bands for h in band]
    if covered != list(range(len(rows))):
        failures.append(
            f"section I bands cover {covered}, expected {list(range(len(rows)))}"
        )
    for step, band in zip(flow, bands):
        band_rows = [rows[h] for h in band]
        common = set(band_rows[0]["actions"])
        for band_row in band_rows[1:]:
            common &= set(band_row["actions"])
        shown_actions = {
            a.strip() for a in re.split(r"[·,]", step["strat"]) if a.strip()
        }
        if not shown_actions <= set(ACTION_ORDER):
            failures.append(
                f"section I {step['num']}: label {step['strat']!r} uses words "
                "outside the hit_tree action vocabulary"
            )
        if len(band) == 1:
            if shown_actions != {band_rows[0]["strategy"]}:
                failures.append(
                    f"section I {step['num']}: label {step['strat']!r} != "
                    f"{band_rows[0]['strategy']!r}"
                )
        elif not shown_actions or not shown_actions <= common:
            failures.append(
                f"section I {step['num']}: label {step['strat']!r} is not true "
                f"of every hit count in the band (common actions {common})"
            )
        allowed_words = {r["top_patterns"][0]["guess3"] for r in band_rows}
        shown_words = {
            w.strip().lower() for w in re.split(r"[/·,]", step["ex"]) if w.strip()
        }
        if shown_words != allowed_words:
            failures.append(
                f"section I {step['num']}: examples {shown_words} != {allowed_words}"
            )
        pct = re.search(r"([\d.]+)%", step["share"])
        left = re.search(r"~\s*([\d.]+)\s*left", step["share"])
        if not pct or not left:
            failures.append(f"section I {step['num']}: share line {step['share']!r}")
        else:
            total_share = sum(r["share_pct"] for r in band_rows)
            if abs(float(pct.group(1)) - round(total_share, 1)) > 0.05:
                failures.append(
                    f"section I {step['num']}: share {pct.group(1)}% != "
                    f"{round(total_share, 1)}%"
                )
            weighted = (
                sum(r["share_pct"] * r["avg_candidates"] for r in band_rows)
                / total_share
            )
            if abs(float(left.group(1)) - weighted) > 0.05:
                failures.append(
                    f"section I {step['num']}: ~{left.group(1)} left != "
                    f"{weighted:.2f}"
                )
        if 5 in band and not re.search(r"anagram|tie", step["note"], re.IGNORECASE):
            failures.append("section I five-hit band lost its anagram-tie caveat")

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
    print("  section I bands, labels and guess-3 words match hit_tree.json")
    print("  section II strategy labels and guess-3 words match hit_tree.json")
    print("  section III counts and action sets match hit_tree.json")
    print("  section IV pattern rows match hit_tree.json")
    print("  rule printed in section III is true of every burn/split word")
    return 0


if __name__ == "__main__":
    sys.exit(main())
