# LedgerLine v1 migration plan

Status: **approved, in progress**
Owner: R. Hamilton (Finance Platform)
Last updated: 2023-02-27

## Goal

Move categorization off the hand-maintained `rules_table.json` and onto a
SQLite-backed rules store so that finance analysts can edit rules without a
code deploy.

Today every rule lives in one of two places:

- `ledgerline/rules_table.json` — the keyword-to-category table loaded at
  startup by `load_rules_table()`
- `ledgerline/classifier.py` — the if/elif ladder that runs when the table
  misses

Neither is editable by anyone outside the team, and the table has drifted from
the ladder in at least a dozen places.

## Target design

```
ledgerline/
  classifier.py      unchanged entry point
  db/
    __init__.py
    schema.sql       rules table DDL
    loader.py        reads rules.db into memory at startup
    admin.py         CLI for analysts to add and disable rules
  rules_table.json   deleted at the end of phase 3
```

The `rules` table carries `keyword`, `category`, `priority` and `enabled`.
Priority replaces the implicit ordering of the if/elif ladder, which is
currently the single biggest source of surprise categorizations.

## Phases

**Phase 1 — schema and loader (target: Q4 2023)**

- [x] Agree the `rules` table schema
- [x] Write `open_rules_db()` and `load_rules_from_db()`
- [ ] Backfill `rules.db` from the current `rules_table.json`
- [ ] Shadow mode: run both paths, log disagreements to
      `/var/log/ledgerline/disagreements.log`, review weekly

**Phase 2 — cutover (target: Q1 2024)**

- [ ] Flip `USE_MCC_CLASSIFICATION` off and read rules from the DB
- [ ] Re-map the `TEL` and `TRN` category codes by hand; there is no v2
      equivalent for either and reports will under-count until this is done
- [ ] Delete `rules_table.json`

**Phase 3 — analyst tooling (target: Q2 2024)**

- [ ] Ship `db/admin.py`
- [ ] Train the two analysts who own category policy
- [ ] Retire the spreadsheet macro that shells out to `legacy_report_row()`

## Open questions

- Do we keep the MCC lookup as a fallback, or drop it once the DB is
  authoritative? The card export has been missing MCC codes since the Q3
  processor migration, so it may be moot.
- Where does `rules.db` live in the deploy? Nobody has claimed this.
- Duplicate detection was supposed to land in the same release. The 3-day
  versus 7-day window question is still open (see `DUPLICATE_WINDOW_DAYS`).

## Rollback

Set `LEGACY_MODE = True` and redeploy. The v1 path is left intact in
`classifier.py` for exactly this reason and should not be deleted until phase 3
has been in production for a full quarter-end close.
