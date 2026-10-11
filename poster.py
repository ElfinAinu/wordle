# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "matplotlib"]
# ///
"""Draft the BLUF-style HTML infographic (dark magical girl theme)."""

import json
from pathlib import Path

import numpy as np

from analyze import (
    ANSWERS_PATH,
    RESULTS_DIR,
    encode,
    letter_counts,
    load_words,
)
from coverage import letter_masks, score_pair
from heatmaps import position_matrix

ROOT = Path(__file__).parent
OUT = ROOT / "infographic.html"

PAIR = ("soare", "clint")
RAMP_FLOOR = 0.05


def ramp(t: float) -> str:
    """Viridis: the standard perceptually uniform colormap of scientific publishing."""
    from matplotlib import colormaps

    r, g, b, _ = colormaps["viridis"](RAMP_FLOOR + (1 - RAMP_FLOOR) * t)
    return f"rgb({round(r * 255)},{round(g * 255)},{round(b * 255)})"


def with_scale(inner: str, vmax: float) -> str:
    stops = ", ".join(f"{ramp(i / 10)} {i * 10}%" for i in range(11))
    return (
        '<div class="hmrow">'
        + inner
        + f'<div class="scale" style="background:linear-gradient(to top, {stops})"></div>'
        + '<div class="scalelabs">'
        + f"<span>{vmax:.0f}%</span><span>{vmax / 2:.0f}%</span><span>0</span></div>"
        + "</div>"
    )


def word_grid_html(matrix: np.ndarray, letters: str) -> str:
    vmax = matrix.max()
    cells = []
    for row, ch in enumerate(letters):
        cells.append(f'<div class="rowlab">{ch.upper()}</div>')
        for pos in range(5):
            value = matrix[row, pos]
            cells.append(
                f'<div class="cell" style="background:{ramp(value / vmax)}" '
                f'title="{ch.upper()} @ pos {pos + 1}: {value:.1f}%"></div>'
            )
    return with_scale('<div class="grid">' + "".join(cells) + "</div>", vmax)


def pair_grid_html(first: str, second: str, matrix: np.ndarray) -> str:
    vmax = matrix.max()
    cells = []
    for word in (first, second):
        for pos, ch in enumerate(word):
            value = matrix[ord(ch) - 97, pos]
            cells.append(
                f'<div class="pcell" style="background:{ramp(value / vmax)}">'
                f"<span>{ch.upper()}</span></div>"
            )
    return with_scale('<div class="pgrid">' + "".join(cells) + "</div>", vmax)


def hit_tree_html(rows: list[dict]) -> str:
    """Render the guess-3 tree branched on hit count (0-5)."""
    out = []
    for row in rows:
        top = row["top_patterns"][0] if row["top_patterns"] else None
        if top:
            guess_cell = (
                f'<span class="tguess">→ {top["guess3"].upper()}</span>'
                f'<span class="tleft">~{top["expected_remaining"]}</span>'
            )
        else:
            guess_cell = '<span class="tguess">just guess it</span>'
        out.append(
            f'<div class="trow"><span class="vkey">{row["hits"]}</span>'
            f'<span class="tshare">{row["share_pct"]}% · ~{row["avg_candidates"]} left</span>'
            f'<span class="tstrat">{row["strategy"]}</span>'
            f"{guess_cell}</div>"
        )
    legend = (
        '<div class="legend">'
        '<span><b class="tstrat">Burn word</b> = test new letters, abandon hitting</span>'
        '<span><b class="tstrat">Split</b> = max-entropy word to divide candidates</span>'
        '<span><b class="tstrat">Guess candidate</b> = play the likeliest remaining word</span>'
        "</div>"
    )
    return (
        '<div class="tree">'
        f'<div class="tnode g1">guess 1 — {PAIR[0].upper()}</div>'
        f'<div class="tnode g2">guess 2 — {PAIR[1].upper()} <i>(fixed, zero shared letters)</i></div>'
        '<div class="tnode g3">guess 3 — count hits (green + yellow letters from both guesses):</div>'
        + "".join(out)
        + "</div>"
        + legend
    )


def hit_table_html(rows: list[dict]) -> str:
    """Render hit-count summary table + per-bucket example patterns."""
    summary = [
        "<table class='htable'><thead><tr>",
        "<th>Hits</th><th>Share</th><th>Patterns</th>",
        "<th>Avg left</th><th>Max left</th><th>Strategy</th>",
        "</tr></thead><tbody>",
    ]
    for row in rows:
        summary.append(
            f"<tr><td class='hnum'>{row['hits']}</td>"
            f"<td>{row['share_pct']}%</td>"
            f"<td>{row['patterns']}</td>"
            f"<td>{row['avg_candidates']}</td>"
            f"<td>{row['max_candidates']}</td>"
            f"<td class='hstrat'>{row['strategy']}</td></tr>"
        )
    summary.append("</tbody></table>")

    details = []
    for row in rows:
        if not row["top_patterns"]:
            continue
        details.append(
            f"<h3>{row['hits']} hits — {row['strategy']} "
            f"<span class='hsub'>{row['share_pct']}% of games</span></h3>"
        )
        details.append(
            "<table class='htable'><thead><tr>"
            "<th>Guess 1</th><th>Pattern</th><th>Guess 2</th><th>Pattern</th>"
            "<th>Cands</th><th>Guess 3</th><th>Left</th>"
            "</tr></thead><tbody>"
        )
        for tp in row["top_patterns"]:
            details.append(
                f"<tr><td>{tp['g1']}</td>"
                f"<td class='hpat'>{tp['g1_pattern']}</td>"
                f"<td>{tp['g2']}</td>"
                f"<td class='hpat'>{tp['g2_pattern']}</td>"
                f"<td>{tp['candidates']}</td>"
                f"<td class='hguess'>{tp['guess3'].upper()}</td>"
                f"<td>~{tp['expected_remaining']}</td></tr>"
            )
        details.append("</tbody></table>")

    return "".join(summary) + "".join(details)


CSS = """
body { margin:0; background:#14171c; color:#dfe3e8;
       font-family:'Helvetica Neue', Arial, sans-serif; }
.wrap { max-width:780px; margin:0 auto; padding:56px 32px 80px; }
h1,h2 { font-family:Georgia,'Times New Roman',serif; font-weight:600; }
h1 { font-size:30px; color:#f0f3f6; text-align:center; margin:0 0 6px; letter-spacing:.02em; }
h1 + .sub { text-align:center; color:#9aa4af; font-size:13px; margin-bottom:36px; }
h2 { font-size:16px; color:#e6edf3; margin:44px 0 12px; border-bottom:1px solid #2d333b;
     padding-bottom:6px; }
.card { background:#1c2026; border:1px solid #2d333b; border-radius:8px; padding:18px 20px; }
.bluf { border-left:4px solid #6ea8fe; font-size:16px; line-height:1.8; }
.bluf b { color:#f0f3f6; font-size:18px; }
.hero { text-align:center; font-size:15px; line-height:1.7; }
.bignum { font-size:52px; color:#6ea8fe; font-family:Georgia,serif; }
.hmrow { display:flex; gap:10px; align-items:stretch; }
.hmrow .grid, .hmrow .pgrid { flex:1; }
.scale { width:14px; border-radius:4px; }
.scalelabs { display:flex; flex-direction:column; justify-content:space-between;
             font-size:10px; color:#9aa4af; }
.grid { display:grid; grid-template-columns:26px repeat(5,1fr); gap:3px; }
.rowlab { display:flex; align-items:center; justify-content:center; color:#9aa4af; font-size:12px; }
.cell { height:20px; border-radius:3px; }
.pgrid { display:grid; grid-template-columns:repeat(5,1fr); gap:6px; margin:10px 0; }
.pcell { height:56px; border-radius:6px; display:flex; align-items:center; justify-content:center; }
.pcell span { font-size:24px; font-family:Georgia,serif; color:#fff; text-shadow:0 1px 3px #000a; }
.stats { display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-top:10px; }
.stat { background:#14171c; border:1px solid #2d333b; border-radius:6px; padding:8px 14px;
        font-size:13px; color:#dfe3e8; }
.stat b { color:#6ea8fe; }
.tree { border-left:2px solid #2d333b; margin-left:6px; padding-left:18px; }
.tnode { margin:8px 0; font-family:Georgia,serif; }
.g1 { color:#f0f3f6; font-size:18px; }
.g2 { color:#6ea8fe; font-size:16px; }
.g2 i { color:#9aa4af; font-size:12px; }
.g3 { color:#9aa4af; font-size:14px; }
.trow { display:grid; grid-template-columns:32px 110px 130px 1fr; gap:10px;
        font-size:13px; padding:5px 0; border-bottom:1px solid #23272e;
        align-items:baseline; }
.vkey { color:#e6edf3; font-family:Georgia,serif; font-size:15px; text-align:center; }
.tshare { color:#9aa4af; white-space:nowrap; }
.tguess { color:#7ee2b8; font-weight:600; white-space:nowrap; }
.tleft { color:#9aa4af; font-size:12px; margin-left:6px; }
.tstrat { color:#c9a227; font-size:13px; white-space:nowrap; }
.legend { display:flex; flex-wrap:wrap; gap:8px 20px; margin-top:12px;
          padding-top:10px; border-top:1px solid #23272e;
          font-size:12px; color:#9aa4af; }
.legend span { white-space:nowrap; }
.htable { width:100%; border-collapse:collapse; font-size:13px; margin:10px 0 18px; }
.htable th { color:#9aa4af; font-weight:600; text-align:left; padding:4px 8px;
             border-bottom:1px solid #2d333b; font-size:11px; text-transform:uppercase; }
.htable td { padding:4px 8px; border-bottom:1px solid #23272e; }
.htable .hnum { color:#6ea8fe; font-family:Georgia,serif; font-size:16px; text-align:center; }
.htable .hstrat { color:#c9a227; }
.htable .hpat { font-family:monospace; letter-spacing:2px; color:#9aa4af; }
.htable .hguess { color:#7ee2b8; font-weight:600; }
.htable h3, h3 { font-size:14px; color:#e6edf3; margin:18px 0 6px; font-family:Georgia,serif; }
.hsub { color:#9aa4af; font-size:12px; font-weight:400; }
ul { margin:8px 0; padding-left:20px; line-height:1.65; font-size:14px; }
li::marker { color:#6ea8fe; }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.dont { color:#ff9b9b; }
.do { color:#7ee2b8; }
footer { margin-top:56px; font-size:11px; color:#9aa4af; text-align:center; line-height:1.8; }
"""


def main() -> None:
    answers = load_words(ANSWERS_PATH)
    matrix = position_matrix(answers)
    order = np.argsort(-matrix.sum(axis=1))
    sorted_letters = "".join(chr(97 + i) for i in order)
    sorted_matrix = matrix[order]

    answer_codes = encode(answers)
    answer_counts = letter_counts(answer_codes)
    masks = letter_masks(answers)
    distinct = masks.sum(axis=1)
    pair_stats = score_pair(
        PAIR[0], PAIR[1], answer_codes, answer_counts, masks, distinct
    )
    hit_rows = json.loads((RESULTS_DIR / "hit_tree.json").read_text())

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Wordle Performance Poster</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Wordle is a Solvable Information Problem</h1>
<div class="sub">a fixed-opening strategy for lowering average guesses · personal reference poster</div>

<div class="card bluf">
  <b>BLUF:</b> play <b>SOARE</b> then <b>CLINT</b>, every game, no thinking.<br>
  count your <b>hits</b> (green + yellow letters) to pick guess 3:<br>
  <b>0</b> → burn word · <b>1</b> → split · <b>2-4</b> → guess candidate · <b>5</b> → solved.<br>
  expect the answer locked by guess 4; {pair_stats["solved_on_two_pct"]}% of games end at guess 2.
</div>

<h2>the play tree</h2>
<div class="card">
  {pair_grid_html(PAIR[0], PAIR[1], matrix)}
  <div class="stats">
    <div class="stat"><b>10</b> letters tested</div>
    <div class="stat"><b>{pair_stats["spot_rate_pct"]}%</b> of answer letters spotted</div>
    <div class="stat"><b>{pair_stats["expected_remaining"]}</b> candidates left</div>
  </div>
  {hit_tree_html(hit_rows)}
</div>

<h2>guess 3 — hit-count reference</h2>
<div class="card">
  {hit_table_html(hit_rows)}
</div>

<h2>why: the ladder</h2>
<div class="card hero">
  <div class="bignum">3.42</div>
  optimal play averages 3.42 guesses and never needs more than 5.<br>
  every 6-guess win was a strategy failure, not a hard word.
  <ul style="text-align:left">
    <li><b>3.42</b> — AI-optimal (SALET, exact solution)</li>
    <li><b>~3.75</b> — WordleBot users, ~¼ guess better than average</li>
    <li><b>~4.1</b> — median human (NYT, 515M games)</li>
    <li><b>&gt;4.5</b> — struggling; losses cluster here</li>
  </ul>
</div>

<h2>why: the letter grid</h2>
<div class="card">
  {word_grid_html(sorted_matrix, sorted_letters)}
  <div class="stats"><div class="stat">color = chance a letter lives in that slot · hover for %</div></div>
</div>

<h2>why: shape grammar</h2>
<div class="card"><ul>
  <li>2 vowels 58% · slots [2,4] most common (31%)</li>
  <li>1-vowel words: vowel in slot 3 (52%) or 2 (41%)</li>
  <li>starts: S 15.8 · C 8.6 · B 7.5 — vowel starts rare</li>
  <li>ends: E 18.3 · Y 15.8 · T 11.0 · R 9.2</li>
</ul></div>

<h2>why: costly mistakes</h2>
<div class="card cols">
  <ul class="dont">
    <li>tunnel vision on one candidate</li>
    <li>reusing gray letters</li>
    <li>changing your opener</li>
  </ul>
  <ul class="do">
    <li>split candidates with a burn word</li>
    <li>treat grays as free info</li>
    <li>watch -E / -ER / -Y and doubles (14.7%)</li>
  </ul>
</div>

<footer>sources: MIT/OR exact Wordle solution · NYT WordleBot &amp; 515M-game analysis ·
3Blue1Brown opener entropy · local analysis of {len(answers)} past answers<br>
pick an opener today and never change it</footer>
</div></body></html>"""

    OUT.write_text(html)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
