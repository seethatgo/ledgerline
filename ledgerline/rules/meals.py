"""Meal rules: restaurants, coffee, food delivery, team catering."""

from ledgerline.legacy_rules import normalize_merchant_name

CATEGORY_NAME = "meals"

MERCHANT_KEYWORDS = (
    "restaurant",
    "cafe",
    "coffee",
    "starbucks",
    "peets",
    "dunkin",
    "blue bottle",
    "panera",
    "chipotle",
    "sweetgreen",
    "mcdonalds",
    "shake shack",
    "pizza",
    "taqueria",
    "sushi",
    "bakery",
    "deli",
    "bistro",
    "diner",
    "grill",
    "brewing",
    "doordash",
    "grubhub",
    "uber eats",
    "caviar",
    "catering",
)

EXCLUDED_KEYWORDS = ()

MEMO_KEYWORDS = (
    "team lunch",
    "client dinner",
    "team breakfast",
    "working lunch",
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
