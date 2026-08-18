# Rule specification

How categorization actually works in LedgerLine 2.x. If something in this
document disagrees with the code, the code is right and this document is a bug.

## The contract

Every module in `ledgerline/rules/` exposes exactly two public names:

| Name | Type | Meaning |
|---|---|---|
| `CATEGORY_NAME` | `str` | the category assigned when the module matches |
| `matches(expense)` | function | `True` if the expense belongs to that category |

`matches()` takes an `Expense` (see `ledgerline/models.py`) and returns a bool.
It must not raise, must not mutate the expense, and must not look at any other
rule module.

## Evaluation order

`ledgerline/engine.py` holds the only ordering that matters:

```python
RULE_MODULES = [travel, meals, office, subscriptions]
```

Evaluation is **first match wins**. The engine walks the list in order and
returns the `CATEGORY_NAME` of the first module whose `matches()` returns
`True`. If no module matches, the expense is left as `uncategorized` and shows
up in the "Needs review" section of the monthly report.

Two consequences worth knowing:

1. Order changes are behaviour changes. Moving `subscriptions` above `office`
   would re-categorize every Amazon charge.
2. Overlaps are resolved by position, not by specificity. `travel` matches on
   `airport`, so a coffee shop inside an airport terminal is categorized as
   travel, not meals.

## The refund short circuit

Before any rule module runs, the engine calls `is_probably_refund()` from
`ledgerline/legacy_rules.py`. Any expense with a negative `amount_cents` is
categorized as `refund` and never reaches the rule modules. Finance reports
credits separately from spend, so this is deliberate.

## Merchant normalization

Rule modules never match against the raw merchant string. They call
`normalize_merchant_name()` from `ledgerline/legacy_rules.py` first, which:

- lowercases and strips surrounding whitespace
- removes a leading payment-processor prefix (`SQ *`, `TST*`, `PAYPAL *`, ...)
- replaces every non-alphanumeric character with a space
- drops purely numeric tokens of three or more digits (store and batch numbers)

So `"TST* PANERA BREAD #2214"` becomes `"panera bread"` and
`"APPLE.COM/BILL"` becomes `"apple com bill"`. Write your keywords against the
normalized form: lowercase, space separated, no punctuation.

`legacy_rules.py` contains several older cleanup functions with similar names
(`normalise_merchant`, `clean_merchant_name`, `scrub_merchant`). None of them
behave the same way. `normalize_merchant_name()` is the only supported one.

## Anatomy of a rule module

All four modules follow the same shape, and new ones should too:

```python
CATEGORY_NAME = "travel"

MERCHANT_KEYWORDS = ("delta air", "marriott", ...)
EXCLUDED_KEYWORDS = ("uber eats",)
MEMO_KEYWORDS = ("conference travel",)

def matches(expense):
    normalized_merchant = normalize_merchant_name(expense.merchant)
    # exclusions first, then merchant keywords, then memo keywords
```

Matching is plain substring containment against the normalized merchant, then
against the lowercased memo. `EXCLUDED_KEYWORDS` wins over everything: it is
how `travel` avoids swallowing Uber Eats orders, since food delivery and
rideshare share a merchant prefix.

Keep keywords specific enough that they cannot appear inside an unrelated
merchant name. A two-letter keyword will match something you did not intend.

## Adding a category

1. Create `ledgerline/rules/<name>.py` following the shape above.
2. Add the module to `RULE_MODULES` in `engine.py`, in the position you want it
   evaluated. This step is easy to forget and the tests will not catch it for
   you unless you add one.
3. Add a test file under `tests/`, including at least one case that the module
   should *not* match.
4. Run the report against `data/` and check the "Needs review" section shrank
   the way you expected.
