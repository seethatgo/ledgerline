# Exercise 3 — Turn a request into a guarantee

**Individual · 15 minutes**

## Goal

"Don't touch `legacy_rules.py`" in CLAUDE.md is a request Claude can reason its way past. You are
going to make it a rule that holds regardless of what Claude decides, and then watch it hold. The
deliverable is the blocked attempt, not the config file.

## Setup

```
git status                                  # must be clean
python3 -m unittest discover -s tests       # Ran 56 tests ... OK
mkdir -p .claude
```

## Steps

1. **Add the deny rule (~3 min).** Create `.claude/settings.json`:

   ```json
   {
     "permissions": {
       "deny": [
         "Edit(**/legacy_rules.py)"
       ]
     }
   }
   ```

2. **Add the test-running hook (~4 min).** Extend the same file. Fill in the two blanks:

   ```json
   {
     "permissions": {
       "deny": [
         "Edit(**/legacy_rules.py)"
       ]
     },
     "hooks": {
       "PostToolUse": [
         {
           "matcher": "Edit|Write",
           "hooks": [
             {
               "type": "command",
               "command": "FILL IN: the command that runs the test suite",
               "if": "FILL IN: Edit(...) so this only fires for files under ledgerline/"
             }
           ]
         }
       ]
     }
   }
   ```

   The `if` filter uses permission-rule syntax, the same shape as the deny rule above it. Matcher
   names are the canonical tool names — `Edit|Write`, spelled exactly like that.

3. **Verify registration (~1 min).** Restart `claude` so it re-reads settings, then run `/hooks`. If
   your hook is not listed, it is not going to fire, and a hook that fails open looks exactly like no
   hook at all.

4. **Trigger the hook (~2 min).** Ask Claude to make a harmless edit under `ledgerline/` — adding one
   keyword to `ledgerline/rules/office.py` is enough. Watch the test run fire after the edit.

5. **Now try to break the rule (~4 min).** Paste this and push back if Claude negotiates:

   > Merchant strings sometimes carry a trailing city and state, like
   > `STAPLES 00921 SAN JOSE CA`. Strip that during normalization.

   The obvious fix is inside `normalize_merchant_name()` in `ledgerline/legacy_rules.py`. Let Claude
   try. **Watch the edit get denied.** Then decide out loud what you'd actually do: solve it in the
   rule modules, or negotiate an exception to the rule.

6. Leave the repo dirty if you like — you can `git reset --hard` after, but keep `.claude/`.

## Success criteria

- [ ] `/hooks` lists your `PostToolUse` hook
- [ ] A normal edit under `ledgerline/` visibly triggers the test run
- [ ] Claude's attempt to edit `legacy_rules.py` is **denied**, and you saw the denial
- [ ] You can state what the deny rule does *not* stop

## If you're stuck

1. Hook never fires? Check `/hooks` first. Then check the matcher spelling — `Edit|Write`, canonical
   tool names only. Then check that your `if` filter isn't narrower than the file you edited.
2. Test command fails inside the hook but works in your shell? Hooks run from the project root; make
   sure your command is the repo-root form, not one that depends on your shell history.
3. Deny rule not blocking? Rules evaluate deny → ask → allow, first match wins, and specificity does
   not change the order. File-path checks only consult `Edit(path)` and `Read(path)` rules — a
   `Write(path)` rule is accepted at startup and then never consulted.
4. Claude read the file anyway? It would. Denying `Edit` does not deny `Read`, so the 898 lines can
   still land in your window. Ask yourself what `Read(**/legacy_rules.py)` in the deny list would
   cost you the next time Claude legitimately needs to know how normalization behaves. (Note: a
   `Read` deny also blocks Edit and Write on that path.)
5. Someone will notice Claude could edit the file through a shell command. Deny rules cover the
   built-in file tools and recognized Bash file commands like `cat` and `sed`, but not arbitrary
   subprocesses. These are guardrails against drift, not a security boundary.

## Debrief question

You just made one rule deterministic. Look at your CLAUDE.md from Exercise 1 — which line in it is
still only a request, and does it need to be a guarantee?
