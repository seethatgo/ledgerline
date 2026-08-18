# LedgerLine

Internal expense categorization rules engine. Takes a corporate card CSV export,
assigns a category to every line, and prints the monthly summary that finance
pastes into the month-end close ticket.

Owned by the Finance Platform team. Python 3, standard library only, no
dependencies to install.

## Quick start

```
python3 run_report.py --file data/expenses_2026_07.csv
```

Run the tests:

```
python3 -m unittest discover -s tests
```

Both commands are run from the repository root.

## What it does

1. `ledgerline/importer.py` reads the CSV export into `Expense` objects.
2. `ledgerline/classifier.py` runs each expense through the rule modules in
   `ledgerline/rules/` and takes the first match.
3. `ledgerline/reports.py` groups the categorized expenses by month and formats
   the plain-text summary.

Anything that matches no rule is left uncategorized and listed at the bottom of
the report so an analyst can look at it.

## Layout

```
ledgerline/
  models.py         Expense and CategoryTotal
  importer.py       CSV -> Expense
  classifier.py     evaluation order, first match wins
  reports.py        monthly summary formatting
  legacy_rules.py   v1 leftovers; two helpers are still live
  rules/
    travel.py
    meals.py
    office.py
    subscriptions.py
docs/               format and rule documentation
data/               sample card exports
tests/              unittest suite
```

## Features

- Keyword-based categorization across four categories
- Merchant string normalization that strips payment-processor prefixes and
  store numbers
- Refund handling: credits are reported separately from spend
- Receipt OCR ingestion for scanned receipts, so paper receipts can be dropped
  into the same pipeline as the card export
- Monthly summary report with a review list for unmatched merchants

## Adding a rule

Read `docs/rules-spec.md` first. In short: add a module under
`ledgerline/rules/` exposing `CATEGORY_NAME` and `matches(expense)`, register it
in the evaluation list, and add a test.

## Gotchas

- Evaluation order is significant. Changing it changes historical reports.
- `legacy_rules.py` is mostly dead code, but not entirely. Check callers before
  deleting anything from it.
- Amounts are integers in cents everywhere inside the package. Only the CSV
  uses dollars.
