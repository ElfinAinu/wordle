# 03: Section VIII - what to do about a repeat

**What to build:** The action half of the new section. First, a strip of shape
templates so the reader recognises the common repeats instead of reading
coordinates: 3-4 at 24% of repeat pairs, 1-5 and 2-5 at about 11% each, shown as
short word templates with the repeated slots marked. Second, the two-copy probe
rule moves out of section VII's mistakes figure into this section, which is
where it belongs, and VII keeps a cross-reference instead of stating it twice.
The rule as written today: to tell one copy of a letter from two, the guess must
carry that letter twice, and the number of non-gray tiles among those two copies
is the number of copies in the answer, with the radar / SOARE / ABACK example.

**Blocked by:** 02 (Section VIII - where repeats occur)

**Status:** ready-for-agent

- [ ] The shape templates strip shows the top three shapes with their shares, as
      templates with the repeated slots marked.
- [ ] The probe rule appears exactly once in the poster - in this section - with
      its worked example intact.
- [ ] Section VII cross-references the rule rather than restating it, and still
      reads correctly on its own.
- [ ] The acceptance check fails if the rule appears in more than one section.
- [ ] All existing checks still pass, and `publish_poster.py --check` still
      passes.
