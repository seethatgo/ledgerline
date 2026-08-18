# Exercise 2 — Hold a long task together

**Individual work, in a breakout room of 3–4 · 30 minutes**

## Goal

Ship a feature that spans several files while deliberately managing the context window instead of
letting it fill up on you. The feature is the excuse; the notes and the compaction are the exercise.

## How the room works

**You work alone, on your own machine, in your own clone and your own `claude` session.** Nobody
drives for anybody. The room exists so you can ask questions out loud, unstick each other fast, and —
at two specific moments below — compare what your sessions did differently. Four people running the
same task and getting four different results is the most useful thing that will happen in this
half hour.

Before you start anything:

```
git status                                  # must be clean
python3 -m unittest discover -s tests       # Ran 56 tests ... OK
python3 run_report.py data/expenses_2026_07.csv
```

Keep that July report visible. `TOTAL $10,117.64 (62)` and six merchants in Needs review is your
before-state.

## The feature

> The card export is adding an optional `recurring` column (`yes`/`no`, absent in older files). Read
> it in the importer into `Expense.is_recurring`, defaulting to `False` when the column or the value
> is missing. A recurring charge that no rule module matches should be categorized as `subscriptions`
> instead of falling through to `uncategorized`. Existing files in `data/` must keep working
> unchanged. Add tests for the importer, the engine, and the subscriptions module.

Files in play: `ledgerline/importer.py`, `ledgerline/models.py`, `ledgerline/engine.py`,
`ledgerline/rules/subscriptions.py`, and `tests/test_importer.py`, `tests/test_engine.py`,
`tests/test_rules_subscriptions.py`.

## How far you need to get

Thirty minutes with twenty people on the same API is not a lot. Get Tier 1 and you have the lesson,
even if the feature is half-built. Do not skip Tier 1 to chase Tier 3.

- **Tier 1 — required. This is the exercise.** `NOTES.md` written *as you go*, one deliberate
  `/compact` at the 15-minute mark, and you can say what the summary kept and what it dropped.
- **Tier 2 — the feature works.** The importer reads the optional `recurring` column into
  `Expense.is_recurring`, defaulting to `False`, and all three existing `data/` files still import
  unchanged.
- **Tier 3 — stretch.** Unmatched recurring charges land in `subscriptions`, with tests added for the
  importer, the engine, and the subscriptions module.

## Steps

1. **0–5 min — plan and open the scratchpad.** Have Claude write `NOTES.md` at the repo root with
   four headings: `Task`, `Decisions made`, `Files touched`, `Next steps`. Fill it in before writing
   any code. Run `/context` and write the number down.
2. **5–15 min — build.** After each meaningful step, tell Claude to update `NOTES.md`. Run the tests
   as you go; they take milliseconds, so there is no excuse not to.
3. **At 15 min — compact, deliberately.** Confirm `NOTES.md` is current *first*. Run `/context` and
   note it. Then:

   ```
   /compact focus on the recurring charge flag
   ```

   **Then talk to your room.** Read your summary out loud. Find one thing your summary kept that
   somebody else's dropped, and one thing yours dropped that theirs kept. You all ran the same task
   for the same fifteen minutes — the summaries will not match, and that is the finding.
4. **15–27 min — finish from the notes.** Keep going in the compacted session. When Claude needs
   something the summary dropped, point it at `NOTES.md` rather than re-explaining. Notice every time
   it re-reads a file it had already read.
5. **27–30 min — verify and compare.** Run the tests and the July report. Run `git diff tests/` and
   confirm no existing test was quietly rewritten to pass. Final `/context`. Then, in the room: what
   did you each have to re-derive after the compact, and could `NOTES.md` have carried it?

## Success criteria

**Tier 1 — do not leave the room without these:**

- [ ] `NOTES.md` was written *as you worked*, not assembled at the end
- [ ] You ran one deliberate `/compact` with a focus instruction at the 15-minute mark
- [ ] You can state one thing the compact summary kept and one thing it dropped
- [ ] You can name one difference between your summary and someone else's in the room
- [ ] `NOTES.md` is specific enough that a brand-new session could resume your work from it alone

**Tier 2:**

- [ ] All three existing files in `data/` still import with no `recurring` column present
- [ ] `python3 -m unittest discover -s tests` still passes

**Tier 3:**

- [ ] A recurring charge that matches no rule module lands in `subscriptions`
- [ ] The suite reports **56 or more** tests, all passing (you added some)
- [ ] `git diff tests/` shows added tests, not edited assertions

## If you're stuck

**Ask your room first.** That is what it is for, and it is faster than chat.

1. `/compact` says "Not enough messages to compact"? Your session is too fresh. Keep working and
   compact when you actually have history.
2. Existing data files break? The column is *optional*. Look at how `parse_expense_rows` checks
   `REQUIRED_COLUMNS` and don't add to that list.
3. Recurring charges still landing in `uncategorized`? The fallback happens in `ledgerline/engine.py`,
   after the `RULE_MODULES` loop. Decide whether the flag belongs there or inside
   `rules/subscriptions.py` — then write the decision in `NOTES.md`, because you will be asked.
4. Lost after the compact? That is the finding, not a failure. Note what was missing from `NOTES.md`
   and add it now.
5. Tests failing on `normalize_merchant_name`? There are several near-identical cleaners in
   `legacy_rules.py`. Only that one is supported.
6. Running behind? Stop at Tier 1 and spend the remaining time on the room comparison. A finished
   feature with no notes is worth less here than notes with a half-finished feature.

## Debrief question

Your compact summary kept some things and dropped others — and so did everyone else's, differently.
Which of the dropped things did you have to re-derive, and could `NOTES.md` have carried it instead?
