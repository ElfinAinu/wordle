# 02: Derive a logically sound guess-3 rule

**What to build:** One stated rule for guess three, derived from the data and
true of every row it is printed beside: what each hit count implies, which
action it takes (burn word, split word, or candidate), and how the recommended
word is chosen. Today the tiers are labelled "Guess candidate" while most
recommended words are not in the candidate pool at all, and for at least one
pattern the recommended word leaves more candidates than simply playing a
candidate would. The output is a reference table — hit count, action,
recommended word, candidates left after it — in which each row's action label is
true of the word shown, plus the one-sentence rule a player applies.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Every recommended word's action label is true of that word: a word
      labelled candidate is in that pattern's candidate pool; a word labelled
      burn or split is not.
- [ ] Where the label says candidate, the recommended word is no worse in
      candidates-left-after than the best in-pool word.
- [ ] The rule is stated in one sentence a player can apply mid-game.
- [ ] The rows displayed are the largest candidate pools for their hit count,
      not a hand-picked subset.
- [ ] The analysis that produces the table emits the action label next to each
      word, so the poster cannot drift from it.
