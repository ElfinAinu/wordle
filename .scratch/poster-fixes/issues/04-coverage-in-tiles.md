# 04: Express letter coverage in tiles, not distinct letters

**What to build:** A coverage figure measured the way the board behaves. The
headline number currently divides by each answer's distinct letters; the share
of tiles actually revealed is lower — roughly 61% against 65% — and the whole
gap is the repeated-letter answers, about a third of the pool, whose second copy
no guess can display. Decide which figure the hero leads with, and where the
number appears, name the metric in words a reader could verify themselves. In
the same pass, the two letter-grid cells rendered as impossible that are not:
one answer puts that letter in that slot, once in the pool.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The coverage analysis reports both the distinct-letter share and the
      tiles-lit share.
- [x] The hero and the opener figure name the metric they use, in words.
- [x] No letter-grid cell is rendered as impossible while an answer does put
      that letter in that slot; the one-word exceptions are visible.
