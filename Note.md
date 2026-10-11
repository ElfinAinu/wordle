# Wordle Performance Infographic — Notes

Long vertical one-pager teaching habits that lower **average guesses**.

Thesis: "Performance" = win rate, average guesses, streak. Streak is luck; win
rate and average guesses are where strategy lives. Hook stat: optimal play
averages **3.42 guesses** and never needs more than 5 — every 6-guess win was a
strategy failure, not a hard word.

## Decision (made)

Audience: **personal desk poster** — denser, reference-style, uses the full
output of the analysis script (frequency charts, opener tables, all mistake
pairs). No compression for phone scrolling.

## Next steps

1. Build an analysis script in this workspace on the real NYT answer list
   (letter frequencies by position, opener rankings, common endings, burn-word
   examples) — data-backed numbers for the graphic.
2. Simulate a few strategies against the answer list to make the benchmark
   ladder real.

## Content outline

### 1. Hero

"Wordle is a solvable information problem." Lead with the 3.42 hook stat.

### 2. Benchmark ladder: how good is your score?

- Ladder: AI-optimal (**3.42**) → WordleBot users (~quarter-guess better than
  average) → median human (~**4.x**, from NYT's 515-million-Wordles analysis) →
  struggling (>4.5 or losses).
- Teach reading distribution shape: front-loaded = skilled, back-loaded = lucky.

### 3. The opener (~40% of your edge)

- Letter frequency chart: overall + by position.
  - Overall most common: **E, A, R, O, T** (E in nearly half of all answers).
  - By position: S starts words; A/O/E/I dominate slot 2; E leads slot 4; E/Y
    end words.
  - Avoid **J, Q, X, Z** in openers.
- Good opener = 5 distinct common letters, ≥2 vowels, no repeats.
- Opener table with avg guesses: **SALET** (optimal) → **TRACE / CRATE / SLATE**
  (near-identical, real words).

### 4. Guesses 1–2 spot letters; guess 3+ solves

- Strategy principle: guesses 1–2 are a **disjoint pair** (no shared letters),
  testing 10 distinct letters to spot which are present — not to reuse or
  solve. Best pairs: **SALON+TRICE**, **CRISE+TALON**, **SCONE+TRAIL**
  (spot ~65% of the answer's letters, leave ~4.4 candidates).
- Alternative for thinkers: adaptive reuse (ROATE tree, leaves ~3.2) —
  stronger raw info, costs a feedback read per game.
- From guess 3: each guess should cross off the largest possible share of
  remaining words.
- Cover the remaining vowels early.
- Treat grays as free information, not waste.

### 5. Endgame: splitting candidates

- Scenario graphic: 3 candidates, 2 guesses left → play a "burn word" testing
  the differing letters instead of praying.
- Watch double letters and common endings (**-E, -ER, -Y**).

### 6. Mistakes that cost you (do/don't pairs)

- Tunnel vision on one candidate.
- Reusing gray letters.
- Changing openers day to day (inconsistency kills data on your own play).
- Hard-mode lock-in traps.
- Panicking into plural forms.

### 7. Footer

Sources + CTA: "Pick an opener today and never change it."

## Deliberately cut

- Exact entropy/bits math — visualize the _behavior_ instead ("this guess
  crossed off 90% of remaining words").
- Streak advice — mostly variance, not skill.

## Verified facts & sources

| Claim                                      | Figure                                             | Source                                                       |
| ------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------ |
| Optimal opener SALET, normal mode          | 3.421 avg guesses, ≤5 guaranteed                   | MIT/OR "An Exact and Interpretable Solution to Wordle"       |
| Optimal opener SALET, hard mode            | 3.5084 avg, may need 6                             | sonorouschocolate.com notes on same paper                    |
| Top letters overall                        | E, A, R, O, T                                      | wordlelist.com/stats, position analyses                      |
| Opener entropy near-optimal (common words) | TRACE, CRATE ≈ SALÉ                                | 3Blue1Brown "Oh wait, actually the best opener is not crane" |
| WordleBot skill benchmark                  | skill 0–99; bot users ~¼ guess faster than average | NYT WordleBot FAQ                                            |
| Median human average                       | ~4.x guesses                                       | NYT "Seven Things We Learned Analyzing 515 Million Wordles"  |

## Glossary

- **Opener** — fixed first guess, chosen for letter coverage, not to hit the
  answer.
- **Grays / greens / yellows** — tile feedback: gray = not in word, yellow = in
  word but wrong spot, green = correct spot.
- **Candidate** — any answer word still consistent with all feedback so far.
- **Burn word** (sacrificial guess) — a guess not meant to win, just to
  eliminate many candidates at once.
- **Hard mode** — every guess must reuse all revealed hints; makes burn words
  illegal late-game, hence "lock-in traps."
- **Entropy / information gain** — how much a guess shrinks the candidate pool;
  higher = more words eliminated per guess.
- **Skill score** — NYT WordleBot's 0–99 rating of guess efficiency vs. the best
  possible move.
- **Average guesses** — mean guesses-to-solve across games; cleanest single
  measure of skill.
