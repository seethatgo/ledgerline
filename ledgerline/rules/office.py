"""Office rules: supplies, hardware, shipping, coworking space."""

from ledgerline.legacy_rules import normalize_merchant_name

CATEGORY_NAME = "office"

MERCHANT_KEYWORDS = (
    "staples",
    "office depot",
    "officemax",
    "best buy",
    "amzn mktp",
    "amazon com",
    "costco",
    "home depot",
    "ikea",
    "uline",
    "monoprice",
    "newegg",
    "b h photo",
    "usps",
    "fedex office",
    "wework",
    "container store",
)

# Cloud infrastructure bills also start with "amazon"; they belong to
# subscriptions, not office supplies.
EXCLUDED_KEYWORDS = (
    "amazon web services",
)

MEMO_KEYWORDS = (
    "office supplies",
    "desk setup",
    "printer paper",
)


def matches(expense):
    normalized_merchant = normalize_merchant_name(expense.merchant)

    for excluded_keyword in EXCLUDED_KEYWORDS:
        if excluded_keyword in normalized_merchant:
            return False

    for keyword in MERCHANT_KEYWORDS:
        if keyword in normalized_merchant:
            return True

    memo_text = (expense.memo or "").lower()
    for keyword in MEMO_KEYWORDS:
        if keyword in memo_text:
            return True

    return False
