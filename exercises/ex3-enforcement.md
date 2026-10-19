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
cat .claude/settings.json                   # already exists - read it before you edit it
```

That file shipped with the repo, and it has been in effect in every session you have run today:

```json
{
  "permissions": {
    "deny": [
      "Read(exercises/**)"
    ]
  }
}
```

That one rule is why your own Claude session could not read the exercise briefs and do your homework
for you. You are about to extend it. **Add to this file — do not overwrite it.**

## Steps

1. **Add your deny rule (~3 min).** Add a second entry to the existing `deny` array so it reads:

   ```json
   {
     "permissions": {
       "deny": [
         "Read(exercises/**)",
         "Edit(**/legacy_rules.py)"
       ]
     }
   }
   ```

2. **Add the test-running hook (~4 min).** Extend the same file. Copy this whole file rather than
   typing it:

   ```json
   {
     "permissions": {
       "deny": [
         "Read(exercises/**)",
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
               "command": "cd \"$CLAUDE_PROJECT_DIR\" && out=$(python3 -m unittest discover -s tests 2>&1) || { echo \"$out\" | tail -15 >&2; exit 2; }"
             }
           ]
         }
       ]
     }
   }
   ```

   What the command does: run the tests after every edit. If they pass, print nothing — zero
   tokens, and Claude never knows it ran. If they fail, send the last 15 lines to Claude with exit
   code 2, which is the code that tells Claude Code "show this to the model." The hook only adds
   context when there is something worth knowing.

3. **Verify registration (~1 min).** Restart `claude` so it re-reads settings, then run `/hooks`. If
   your hook is not listed, it is not going to fire, and a hook that fails open looks exactly like no
   hook at all.

4. **Make the hook speak (~2 min).** Ask Claude for an edit that breaks a test:

   > Change CATEGORY_NAME in ledgerline/rules/office.py to "office_supplies". Don't run anything
   > yourself.

   Two tests assert that the category is `"office"`, so they fail. You never asked for a test run,
   but Claude gets the failure from the hook and tells you about it — and usually offers to fix it.
   Let it revert the change, or reset the file yourself with
   `git checkout ledgerline/rules/office.py`.

5. **Now try to break the rule (~4 min).** Paste this and push back if Claude negotiates:

   > Merchant strings sometimes carry a trailing city and state, like
   > `STAPLES 00921 SAN JOSE CA`. Strip that during normalization.

   The obvious fix is inside `normalize_merchant_name()` in `ledgerline/legacy_rules.py`. Let Claude
   try. **Watch the edit get denied.** Then decide out loud what you'd actually do: solve it in the
   rule modules, or negotiate an exception to the rule.

6. Leave the repo dirty if you like. Note that `git reset --hard` reverts `settings.json` to the
   shipped one-rule version, because it is a tracked file — so if you want to keep your hook, save a
   copy somewhere outside the repo before resetting.

## Success criteria

- [ ] `/hooks` lists your `PostToolUse` hook
- [ ] The category rename makes Claude report failing tests you never asked it to run
- [ ] Claude's attempt to edit `legacy_rules.py` is **denied**, and you saw the denial
- [ ] `Read(exercises/**)` is still in your deny array — you extended the file rather than replacing it
- [ ] You can state what the deny rule does *not* stop

## If you're stuck

1. Hook never fires? Check `/hooks` first. Then check the matcher spelling — `Edit|Write`, canonical
   tool names only — and that you restarted `claude` after saving the file.
2. Nothing happened after a harmless edit? That's correct: the hook is silent when the tests pass.
   Press Ctrl+O after an edit to see that it ran.
3. Claude Code says the settings file is invalid? You probably dropped a quote or a backslash in the
   command. Paste the whole file from this brief again.
4. Deny rule not blocking? Rules evaluate deny → ask → allow, first match wins, and specificity does
   not change the order. File-path checks only consult `Edit(path)` and `Read(path)` rules — a
   `Write(path)` rule is accepted at startup and then never consulted.
5. Claude read the file anyway? It would. Denying `Edit` does not deny `Read`, so the 898 lines can
   still land in your window. Ask yourself what `Read(**/legacy_rules.py)` in the deny list would
   cost you the next time Claude legitimately needs to know how normalization behaves. (Note: a
   `Read` deny also blocks Edit and Write on that path.)
6. Someone will notice Claude could edit the file through a shell command. Deny rules cover the
   built-in file tools and recognized Bash file commands like `cat` and `sed`, but not arbitrary
   subprocesses. These are guardrails against drift, not a security boundary.

## Debrief question

You just made one rule deterministic. Look at your CLAUDE.md from Exercise 1 — which line in it is
still only a request, and does it need to be a guarantee?
