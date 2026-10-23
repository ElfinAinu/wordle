# 01: Measure how repeats are shaped

**What to build:** The fact source for a new poster section on letter repeats.
The existing duplicate analysis reports how often repeats happen and whether the
copies touch, but not where they sit or whether the reader could have noticed
them. Extend it to emit, as both markdown and json under `results/`: the
distribution over slot pairs, the shape list at the level of a repeated letter,
the touching/separated split by letter class, and the visibility split against
the fixed opening. Everything must be recomputable from the committed answer
list.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

Values the implementation must reproduce - verify these, do not transcribe them:

- 747 answers (32.4%) contain a repeat; 786 repeated-letter instances; 826
  repeat pairs (a letter appearing three times contributes three pairs).
- Slot pairs, share of all repeat pairs: 3-4 198 (24.0%); 1-4 95 and 1-5 95
  (11.5% each); 2-5 92 (11.1%); 2-4 82 (9.9%); 1-3 78 (9.4%); 4-5 72 (8.7%); 2-3
  68 (8.2%); 3-5 44 (5.3%); 1-2 2 (0.2%).
- Touching 340 instances against separated 446 - so most repeats are not
  doubles.
- Among touching repeats: 222 consonant, 118 vowel. Among separated: 238 vowel,
  200 consonant.
- Against the opening's ten letters: 639 instances (81.3%) repeat a letter that
  is tested, meaning one copy can show and the count still cannot be read; 147
  (18.7%) repeat a letter never tested, so nothing shows at all.

- [ ] The slot-pair distribution, the shape list, the class split and the
      visibility split are written to `results/` as markdown and json.
- [ ] Every figure above reproduces from `data/answers.txt`.
- [ ] Each output states which universe and which opening pair it is measured
      against.
- [ ] Regenerating twice produces identical output.
