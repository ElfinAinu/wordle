# 13: Regenerate every result the old feedback computed

**What to build:** Once the shared feedback function is correct, every result
whose search ranged over guesses that repeat a letter was computed against wrong
feedback and must be regenerated and diffed: the pair tree (it prints
repeated-letter picks such as TWEEL, ATTAR and AAHED), the opener ranking, both
disjoint-pair scans, and the vowel and all-gray outputs. The hit tree and the
simulation must now agree with the shared function exactly rather than through a
private copy. Report what moved and why, per file — a number that changes is a
finding to explain, not a silent update. If any figure the poster publishes
moves, say so explicitly instead of absorbing it.

**Blocked by:** 12 (Make the shared feedback function correct when the guess
repeats a letter)

**Status:** ready-for-agent

- [ ] Every result file whose computation touched a repeated-letter guess is
      regenerated.
- [ ] Each regenerated file is diffed against its previous version, with the
      movement explained per file.
- [ ] Any published poster figure that moves is reported explicitly, and the
      poster is corrected only if the movement is real.
- [ ] The full check suite passes, and regenerating twice produces identical
      output.
