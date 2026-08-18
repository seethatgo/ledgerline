# Exercise 1 — Write a CLAUDE.md for LedgerLine

**Individual · 20 minutes**

## Goal

Run the same task twice — once on the bare repo, once with a CLAUDE.md you wrote — and measure the
difference with `/context` instead of guessing at it. You are not trying to write a good document;
you are trying to find the smallest set of facts that changes Claude's behaviour.

## Setup

From your own clone, at the repo root:

```
git status                                  # must be clean
ls CLAUDE.md                                # must NOT exist yet
python3 -m unittest discover -s tests       # Ran 56 tests ... OK
python3 run_report.py data/expenses_2026_05.csv
```

The last command prints a "Needs review" list. `AT&T MOBILITY` and `VERIZON WIRELESS` are on it
(May has AT&T, June and July have Verizon). That is the task.

## Steps

1. **Baseline run, no CLAUDE.md (~6 min).** Start a fresh `claude` session and paste exactly:

   > Read README.md, then add a telecom category so VERIZON WIRELESS and AT&T MOBILITY stop landing
   > in the Needs review list.

   Let it plan and make its first edits. Do **not** correct it. Write down four things: which module
   name it used for the evaluation order, whether it touched `ledgerline/legacy_rules.py`, whether it
   registered the new module anywhere, and whether the report output actually changed.

2. Run `/context`. Note the total and note what appears — or doesn't — under **Memory files**.

3. **Reset.** `git reset --hard && git clean -fd`, then `/exit`. Do this *before* you write your
   CLAUDE.md — `git clean -fd` deletes untracked files.

4. **Write `./CLAUDE.md` (~7 min). Under 30 lines.** It must cover, at minimum:
   - the test command and the report command students and Claude should use
   - which file actually owns the evaluation order, and the name the README gets wrong
   - the interface a `ledgerline/rules/*.py` module has to expose, and the fact that a new module is
     invisible until it is registered
   - a warning about how far to trust `README.md`

   Constraints: do not paste the README into it. Do not paste any of `legacy_rules.py` into it. Every
   line has to be a fact Claude cannot cheaply discover on its own, or it is not paying rent.

5. **Re-run (~5 min).** Fresh `claude` session. Run `/context` first and confirm your file is listed
   under Memory files. Then paste the *identical* prompt from step 1.

6. **Compare (~2 min).** Diff the two runs against your notes from step 1, and diff the `/context`
   totals. Then answer this in one line, for yourself: what did you deliberately leave out of
   CLAUDE.md, and why?

## Success criteria

- [ ] `/context` shows `CLAUDE.md` under **Memory files** in the second session
- [ ] The second run does not invent `classifier.py`, and does not put keywords into `legacy_rules.py`
- [ ] The second run registers the new rule module so the report output actually changes
- [ ] `python3 -m unittest discover -s tests` still passes
- [ ] Your CLAUDE.md is under 30 lines and you can name one thing you left out and defend the choice

## If you're stuck

1. Nothing under Memory files? Check the file is at the repo root, named exactly `CLAUDE.md`, and
   that you started a new session after writing it. Memory loads at launch.
2. Baseline run looked *fine*? Check harder. Run the report and compare the Needs review list before
   and after — a new module that was never registered changes nothing and breaks no tests.
3. Can't tell what to put in the file? Compare `README.md` against `ledgerline/` yourself. Every
   place they disagree is a candidate line.
4. Over 30 lines? Delete anything Claude could find with one grep. Facts about *naming* and
   *registration* survive that test; restating what a function does usually doesn't.

## Debrief question

Your CLAUDE.md is paid for on every single request. Pick the one line in yours you would defend to a
teammate who wants to delete it — and say what it prevents.
