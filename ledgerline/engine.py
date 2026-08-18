"""The categorization engine.

Every expense is run through the rule modules in RULE_MODULES order and the
first module whose matches() returns True wins. Anything that matches nothing
is left as "uncategorized" for a human to review.

The evaluation contract is written up in docs/rules-spec.md.
"""

from ledgerline.legacy_rules import is_probably_refund, normalize_merchant_name
from ledgerline.models import UNCATEGORIZED
from ledgerline.rules import meals, office, subscriptions, travel

# Order matters: the first module that matches an expense wins.
RULE_MODULES = [travel, meals, office, subscriptions]

REFUND_CATEGORY = "refund"


def categorize(expense):
    """Return the category name for a single expense."""
    # Credits and chargebacks never go through the rule modules; finance wants
    # them reported separately from real spend.
    if is_probably_refund(expense.amount_cents):
        return REFUND_CATEGORY

    for rule_module in RULE_MODULES:
        if rule_module.matches(expense):
            return rule_module.CATEGORY_NAME
    return UNCATEGORIZED


def categorize_all(expenses):
    """Return a new list of expenses with categories filled in."""
    categorized = []
    for expense in expenses:
        categorized.append(expense.with_category(categorize(expense)))
    return categorized


def matching_module_name(expense):
    """Return the name of the rule module that claimed this expense, or None."""
    if is_probably_refund(expense.amount_cents):
        return None
    for rule_module in RULE_MODULES:
        if rule_module.matches(expense):
            return rule_module.__name__
    return None


def explain(expense):
    """One-line, human-readable account of how an expense was categorized.

    Used by run_report.py --explain and by anyone debugging a surprising
    category in a monthly report.
    """
    category = categorize(expense)
    module_name = matching_module_name(expense)
    source = module_name if module_name else "no rule module matched"
    return "%s -> %s (normalized merchant: %r, matched by: %s)" % (
        expense.merchant,
        category,
        normalize_merchant_name(expense.merchant),
        source,
    )
