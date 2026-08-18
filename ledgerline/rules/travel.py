"""Travel rules: flights, hotels, rental cars, rideshare, rail."""

from ledgerline.legacy_rules import normalize_merchant_name

CATEGORY_NAME = "travel"

MERCHANT_KEYWORDS = (
    "delta air",
    "united air",
    "american airlines",
    "southwest air",
    "alaska air",
    "jetblue",
    "air canada",
    "expedia",
    "marriott",
    "hilton",
    "hyatt",
    "westin",
    "courtyard",
    "airbnb",
    "hertz",
    "avis rent",
    "enterprise rent",
    "amtrak",
    "uber",
    "lyft",
    "airport",
    "parking garage",
    "taxi",
)

# Food delivery runs under the same merchant prefixes as rideshare, so it has
# to be excluded here or travel would swallow every dinner order.
EXCLUDED_KEYWORDS = (
    "uber eats",
    "ubereats",
)

MEMO_KEYWORDS = (
    "conference travel",
    "offsite flight",
    "hotel stay",
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
