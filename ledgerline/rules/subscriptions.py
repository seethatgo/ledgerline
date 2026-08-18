"""Subscription rules: SaaS seats, cloud infrastructure, developer tooling."""

from ledgerline.legacy_rules import normalize_merchant_name

CATEGORY_NAME = "subscriptions"

MERCHANT_KEYWORDS = (
    "github",
    "gitlab",
    "atlassian",
    "jetbrains",
    "adobe",
    "figma",
    "notion",
    "slack",
    "zoom us",
    "zoom video",
    "dropbox",
    "google workspace",
    "amazon web services",
    "datadog",
    "pagerduty",
    "twilio",
    "sentry",
    "miro",
    "1password",
    "apple com bill",
)

EXCLUDED_KEYWORDS = ()

MEMO_KEYWORDS = (
    "monthly subscription",
    "annual license",
    "seat license",
    "saas renewal",
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
