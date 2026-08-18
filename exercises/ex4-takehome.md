# Exercise 4 — Stale-doc audit (take-home)

**Solo · ~45 minutes · no due date, but do it before you forget the `/context` habit**

## Goal

Documentation that contradicts the code is worse than no documentation, because Claude will believe
it. Audit every claim in `README.md` and `docs/` against the actual source, then fix the README.

## Setup

Work from a clean clone so your Exercise 1–3 files aren't in the way:

```
git reset --hard && git clean -fd
git status                                  # must be clean
python3 -m unittest discover -s tests       # Ran 56 tests ... OK
python3 run_report.py data/expenses_2026_07.csv
```

In scope: `README.md`, `docs/rules-spec.md`, `docs/data-format.md`, `docs/categorization-faq.md`,
`docs/v1-migration-plan.md`.

Nobody is going to tell you which of those are wrong or how many errors there are. Finding out is the
assignment.

## Steps

1. **Audit.** Have Claude Code verify each claim in those five files against the code. Every finding
   needs three parts: the claim (file plus line), the contradicting evidence (source file plus the
   symbol or line that proves it), and a proposed fix. A finding without a code citation is a guess.
2. **Watch how it retrieves.** Note whether Claude reads whole files or globs and greps for the
   symbol in the claim. Note what `/context` says when you're done. You will use this later on a real
   repo where reading everything is not an option.
3. **Also record what's correct.** At least one file in `docs/` is accurate. Say which, and say how
   you verified it — "I didn't find anything wrong" is not verification.
4. **Write the report** to `docs-audit.md` at the repo root. Group by file. Mark each finding as
   confirmed-against-code or unverified.
5. **Fix `README.md` only.** Do not touch `docs/` — deciding who owns those files is part of the
   answer, not your call. Where a claim describes a feature that does not exist, the fix is deleting
   the claim, not building the feature.
6. **Re-verify.** Every command you leave in the README must run. Paste it into your shell and check
   the exit code. Then run the test suite one more time.
7. **One paragraph, at the bottom of `docs-audit.md`:** how should this repo stop docs from drifting
   again? Name the mechanism, not the intention — you now know the difference between a request and a
   guarantee.

## Success criteria

- [ ] Your audit finds at least one **command in the README that does not work as written**. Run every
      command in the README and check its exit code; if you found none, you didn't run them.
- [ ] Your audit finds at least one **feature claimed in the README that does not exist in the code**.
      If you found none, grep for the implementation before you accept the claim.
- [ ] Your audit finds at least one **module name in the README that does not exist**, and catches
      *every* place it appears.
- [ ] Your audit finds **multiple** wrong answers in `docs/categorization-faq.md` — not one. Most of
      that file is correct, which is exactly why people stop looking after the first error. If you
      found one or two, go back and check every single claim against `ledgerline/engine.py`,
      `ledgerline/models.py`, and `ledgerline/reports.py`.
- [ ] Your audit flags `docs/v1-migration-plan.md` and says something about the *paths* it references
      and its *status*, not just that it's old.
- [ ] Every finding cites a source file and symbol. Count your findings. If you have fewer than ten
      across all five files, you stopped early — say why you think you're done.
- [ ] `README.md` is fixed, every command in it runs clean, and `python3 -m unittest discover -s tests`
      still passes.
- [ ] `docs-audit.md` names which docs are *accurate* and how you established that.

## If you're stuck

1. Don't know where to start? Take one claim at a time and ask "what file would prove this?" That
   question is the whole method.
2. Claude agreeing with the docs? You probably gave it the doc as context and asked it to check
   itself. Ask it to read the code first and describe the behaviour, *then* compare to the doc.
3. Audit came back short? Try it per-file instead of all at once, or per-question for the FAQ. A claim
   count of one per file usually means the model summarized instead of enumerating.
4. Can't tell whether a doc claim about report output is right? Run
   `python3 run_report.py data/expenses_2026_07.csv` and read the actual output. Same for
   `--explain`. The code is right there and it runs in under a second.
5. Tempted to implement a missing feature so the doc becomes true? Stop. Write down who would have to
   approve that decision, and delete the claim instead.
