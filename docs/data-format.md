# Expense CSV format

What `ledgerline/importer.py` expects, and what the card processor actually
sends us. Sample files live in `data/`.

## Columns

The file must have a header row. Four columns are required, and column order
does not matter because the importer reads by name:

| Column | Required | Example | Notes |
|---|---|---|---|
| `date` | yes | `2026-07-14` | ISO `YYYY-MM-DD` only |
| `merchant` | yes | `TST* PANERA BREAD #2214` | raw processor string, not cleaned |
| `amount` | yes | `48.90` | dollars, not cents |
| `memo` | yes (may be empty) | `team lunch` | free text from the submitter |

Header names are matched case-insensitively and surrounding whitespace is
stripped. Any extra columns are ignored. A missing required column raises
`ExpenseImportError` naming the columns that were absent.

## Dates

ISO `YYYY-MM-DD`, parsed with `datetime.date.fromisoformat`. The v1 importer
accepted `MM/DD/YYYY` as well; the current one does not, and will raise
`ExpenseImportError` with the offending line number.

## Amounts

Amounts arrive as dollar strings and are stored on the `Expense` as whole cents
in `amount_cents`. Accepted decorations:

- a leading `$` (`$48.90`)
- thousands separators (`1,240.11`)
- a leading sign (`-412.30`, `+18.00`)
- a missing decimal part (`96` becomes `9600`)
- a single decimal digit (`5.5` becomes `550`)

Parsing is done on the string, never through `float()`, so a value like `0.07`
cannot drift by a cent. More than two decimal places is an error rather than a
rounding decision.

**Negative amounts are credits.** They are categorized as `refund` and skip the
rule modules entirely. See `docs/rules-spec.md`.

## Merchant strings

Merchant strings come through exactly as the processor sends them, including
prefixes and store numbers:

```
SQ *BLUE BOTTLE COFFEE
TST* PANERA BREAD #2214
AMZN MKTP US*2X3AB9QQ1
DELTA AIR 0062378891234
```

Do not clean them up in the CSV. Normalization is the rule engine's job, and
the raw string is what the report prints in the "Needs review" section so a
human can look it up in the card portal.

## Rows

- Blank rows are skipped, including the trailing newline most exports end with.
- An empty `memo` is fine; an empty `merchant` is not.
- Rows are not deduplicated. The same charge appearing twice will be counted
  twice.
- One file may span more than one month. `run_report.py` groups by month and
  prints a section per period, oldest first.

## Example

```csv
date,merchant,amount,memo
2026-07-01,GITHUB INC,92.00,team seats
2026-07-02,DELTA AIR 0062378899102,521.60,conference travel
2026-07-03,SQ *STARBUCKS AIRPORT T2,11.85,
2026-07-26,BEST BUY REFUND 00445,-149.99,webcams returned
```
