"""Legacy rule logic carried over from LedgerLine v1 (and parts of v0).

WARNING
-------
This module is mostly dead. It is kept in the tree because a small number of
helpers are still imported by ledgerline/engine.py and by the rules package,
and because the 2024 batch reconciliation job used to import several of the
older classify_* functions directly. Nobody has confirmed that the batch job is
switched off, so deletions have been deferred three quarters in a row.

Still live (do not remove without checking callers):
    normalize_merchant_name()
    is_probably_refund()

Everything else in here should be considered historical. If you are adding new
categorization behaviour, add it under ledgerline/rules/ instead and read
docs/rules-spec.md first.

History
    v0.4  2019  first pass, single classify_expense() with an if/elif ladder
    v1.0  2021  MCC-code driven classification, rules_table.json lookups
    v1.4  2022  merchant string normalization added (the only part that stuck)
    v2.0  2023  rewrite into ledgerline/rules/, legacy path left in place
    v2.4  2025  engine.py became the only supported entry point

TODO(dpatel, 2022-11-02): delete the MCC path once the card export includes
    merchant category codes again. It has not since the Q3 processor migration.
TODO(rhamilton, 2023-06-14): the v2 classifier below disagrees with the new
    rules package on hotel F&B charges. Reconcile before the v2 cutover.
TODO(unassigned): nobody knows who owns this file anymore.
"""

# The v1 batch job used to load a JSON rules table shipped alongside the
# package. The module was removed in 2.1 but the import guard stayed so the
# old job would fail soft instead of crashing the nightly run.
try:
    from ledgerline import rules_table  # type: ignore
    HAS_RULES_TABLE = True
except ImportError:
    rules_table = None
    HAS_RULES_TABLE = False


# ---------------------------------------------------------------------------
# Feature flags
#
# These were read from the environment in v1. The environment lookups were
# removed when the config service was decommissioned; the constants stayed.
# ---------------------------------------------------------------------------

LEGACY_MODE = False
USE_MCC_CLASSIFICATION = False
STRICT_MERCHANT_MATCHING = False
ENABLE_FUZZY_FALLBACK = False
DOUBLE_CHECK_AGAINST_V1 = False
EMIT_CLASSIFICATION_METRICS = False


# ---------------------------------------------------------------------------
# Category names
#
# v1 used short codes; v2 uses the long names defined on the rule modules.
# The mapping below is what the migration script would have used.
# ---------------------------------------------------------------------------

CATEGORY_TRAVEL = "TRV"
CATEGORY_MEALS = "MEA"
CATEGORY_OFFICE = "OFF"
CATEGORY_SOFTWARE = "SFW"
CATEGORY_TELECOM = "TEL"
CATEGORY_TRAINING = "TRN"
CATEGORY_MISC = "MSC"
CATEGORY_UNKNOWN = "UNK"

V1_TO_V2_CATEGORY_NAMES = {
    CATEGORY_TRAVEL: "travel",
    CATEGORY_MEALS: "meals",
    CATEGORY_OFFICE: "office",
    CATEGORY_SOFTWARE: "subscriptions",
    # TEL and TRN never got v2 equivalents. Expenses in those categories were
    # supposed to be re-mapped by hand during the v2 cutover, which did not
    # happen, so historical reports under-count office spend.
    CATEGORY_TELECOM: "office",
    CATEGORY_TRAINING: "office",
    CATEGORY_MISC: "uncategorized",
    CATEGORY_UNKNOWN: "uncategorized",
}


# ---------------------------------------------------------------------------
# Merchant string cleanup (LIVE)
#
# This is the one piece of v1 that the current engine still depends on.
# Card processors decorate merchant names with their own prefixes and with
# store numbers, so raw strings look like:
#
#     "SQ *BLUE BOTTLE COFFEE"
#     "TST* PANERA BREAD #2214"
#     "AMZN MKTP US*2X3AB9QQ1"
#     "DELTA AIR 0062378891234"
#
# normalize_merchant_name() flattens all of those to lowercase words so the
# rule modules can do plain substring checks.
# ---------------------------------------------------------------------------

PAYMENT_PROCESSOR_PREFIXES = (
    "sq *", "sq*", "tst* ", "tst*", "paypal *", "paypal*",
    "pp*", "sp ", "sp*", "chk*", "pos ", "dd *",
)

# Tokens that are pure noise from the processor: store numbers, batch ids and
# terminal ids. Anything numeric this long is never part of a brand name.
MINIMUM_STORE_NUMBER_LENGTH = 3


def normalize_merchant_name(raw_merchant):
    """Flatten a raw card merchant string to lowercase, punctuation-free words.

    Called by engine.explain() and by every module in ledgerline/rules/.
    """
    text = (raw_merchant or "").strip().lower()

    text = strip_processor_prefix(text)
    text = replace_punctuation_with_spaces(text)

    kept_tokens = []
    for token in text.split():
        if is_store_number_token(token):
            continue
        kept_tokens.append(token)
    return " ".join(kept_tokens)


def strip_processor_prefix(text):
    """Remove a single leading payment-processor prefix if one is present."""
    for prefix in PAYMENT_PROCESSOR_PREFIXES:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return text


def replace_punctuation_with_spaces(text):
    """Turn every non-alphanumeric character into a space."""
    cleaned_characters = []
    for character in text:
        if character.isalnum() or character.isspace():
            cleaned_characters.append(character)
        else:
            cleaned_characters.append(" ")
    return "".join(cleaned_characters)


def is_store_number_token(token):
    """True for tokens that are just digits, such as store or batch numbers."""
    return token.isdigit() and len(token) >= MINIMUM_STORE_NUMBER_LENGTH


# ---------------------------------------------------------------------------
# Refund detection (LIVE)
#
# Finance reports credits separately from spend. In the current card export a
# credit is simply a negative amount; in the v1 export it was a positive amount
# with a "CR" suffix on the merchant string, which is why the old helper below
# takes a whole row instead of an amount.
# ---------------------------------------------------------------------------


def is_probably_refund(amount_cents):
    """True when an amount represents a credit rather than real spend."""
    return amount_cents < 0


def is_probably_refund_v1(row):
    """Old row-shaped refund check. Unused since the v1 export was retired."""
    merchant = (row.get("merchant") or "").upper()
    if merchant.endswith(" CR"):
        return True
    if merchant.endswith("-CR"):
        return True
    if "REFUND" in merchant:
        return True
    if "REVERSAL" in merchant:
        return True
    return False


def is_credit(amount_cents):
    """Near-duplicate of is_probably_refund kept for the old batch job.

    Note the off-by-one: this one treats a zero-dollar authorisation as a
    credit, which is why the 2022 reports showed phantom refunds.
    """
    return amount_cents <= 0


# ---------------------------------------------------------------------------
# Merchant cleanup, older attempts
#
# Three of these predate normalize_merchant_name. They all look almost right
# and all behave slightly differently. Do not swap one in for another.
# ---------------------------------------------------------------------------


def normalise_merchant(raw_merchant):
    """v1.2 spelling of the cleanup helper.

    Differs from normalize_merchant_name in two ways that matter: it does not
    strip processor prefixes, and it keeps punctuation, so "APPLE.COM/BILL"
    comes back as "apple.com/bill" instead of "apple com bill".
    """
    if raw_merchant is None:
        return ""
    return " ".join(raw_merchant.lower().split())


def clean_merchant_name(raw_merchant):
    """v1.3 cleanup. Strips digits everywhere, including inside brand names,
    so "7-ELEVEN" becomes "eleven" and "1PASSWORD" becomes "password".
    """
    text = (raw_merchant or "").lower()
    cleaned_characters = []
    for character in text:
        if character.isdigit():
            continue
        if character.isalpha() or character.isspace():
            cleaned_characters.append(character)
        else:
            cleaned_characters.append(" ")
    return " ".join("".join(cleaned_characters).split())


def scrub_merchant(raw_merchant):
    """v0.9 cleanup. Truncates to 24 characters because the old UI column was
    24 characters wide. Nothing should be using this.
    """
    return clean_merchant_name(raw_merchant)[:24]


def merchant_key(raw_merchant):
    """Stable dictionary key for a merchant. Used only by the dead MCC path."""
    return normalise_merchant(raw_merchant).replace(" ", "_")


# ---------------------------------------------------------------------------
# MCC (merchant category code) tables
#
# The card export stopped including MCC codes after the Q3 2022 processor
# migration, so everything below is unreachable in practice.
# ---------------------------------------------------------------------------

MCC_TRAVEL_CODES = (
    "3000", "3001", "3005", "3008", "3058", "3501", "3502", "3509",
    "4111", "4121", "4131", "4511", "4582", "4722", "4784",
)
MCC_MEAL_CODES = ("5811", "5812", "5813", "5814", "5499")
MCC_OFFICE_CODES = ("5943", "5044", "5045", "5111", "5200", "5712", "7311")
MCC_SOFTWARE_CODES = ("5734", "5817", "5818", "7372")
MCC_TELECOM_CODES = ("4812", "4813", "4814", "4899")
MCC_TRAINING_CODES = ("8220", "8241", "8244", "8249", "8299")

MCC_TO_CATEGORY = {}
for _code_group, _category in (
    (MCC_TRAVEL_CODES, CATEGORY_TRAVEL),
    (MCC_MEAL_CODES, CATEGORY_MEALS),
    (MCC_OFFICE_CODES, CATEGORY_OFFICE),
    (MCC_SOFTWARE_CODES, CATEGORY_SOFTWARE),
    (MCC_TELECOM_CODES, CATEGORY_TELECOM),
    (MCC_TRAINING_CODES, CATEGORY_TRAINING),
):
    for _mcc_code in _code_group:
        MCC_TO_CATEGORY[_mcc_code] = _category

# Codes we saw in production but never mapped. The nightly job logged these to
# a file nobody read.
UNMAPPED_MCC_CODES = (
    "5192", "5300", "5310", "5411", "5541", "5661", "5732",
    "5921", "5977", "6012", "7230", "7392", "7995", "9399",
)


def category_for_mcc(mcc_code):
    """Look up a merchant category code. Dead: the export no longer has MCCs."""
    if not USE_MCC_CLASSIFICATION:
        return CATEGORY_UNKNOWN
    return MCC_TO_CATEGORY.get(str(mcc_code).strip(), CATEGORY_UNKNOWN)


def category_for_mcc_with_fallback(mcc_code, merchant):
    """MCC lookup that falls back to the v1 keyword ladder. Dead."""
    category = category_for_mcc(mcc_code)
    if category != CATEGORY_UNKNOWN:
        return category
    return classify_expense_v1(merchant, 0, "")


# ---------------------------------------------------------------------------
# v1 keyword tables
#
# Superseded by the per-module keyword tuples in ledgerline/rules/. These are
# kept because the v1 classifiers below still reference them, and the v1
# classifiers are kept because of the batch job nobody has confirmed is off.
# ---------------------------------------------------------------------------

V1_TRAVEL_KEYWORDS = (
    "AIRLINE", "AIR LINES", "DELTA", "UNITED", "AMERICAN AIR", "SOUTHWEST",
    "JETBLUE", "ALASKA AIR", "HOTEL", "MARRIOTT", "HILTON", "HYATT",
    "SHERATON", "WESTIN", "RESIDENCE INN", "RENTAL", "HERTZ", "AVIS",
    "NATIONAL CAR", "UBER", "LYFT", "TAXI", "AMTRAK", "PARKING", "TOLL",
    "HOTEL", "UBER",
)

V1_MEAL_KEYWORDS = (
    "RESTAURANT", "CAFE", "COFFEE", "STARBUCKS", "PEETS", "DUNKIN",
    "PANERA", "CHIPOTLE", "PIZZA", "GRILL", "DELI", "BAKERY", "SUSHI",
    "TAQUERIA", "DOORDASH", "GRUBHUB", "SEAMLESS", "CATERING",
)

V1_OFFICE_KEYWORDS = (
    "STAPLES", "OFFICE DEPOT", "OFFICEMAX", "BEST BUY", "AMAZON", "AMZN",
    "COSTCO", "HOME DEPOT", "IKEA", "ULINE", "FEDEX", "UPS STORE", "USPS",
)

V1_SOFTWARE_KEYWORDS = (
    "GITHUB", "ATLASSIAN", "JIRA", "ADOBE", "MICROSOFT", "GOOGLE",
    "DROPBOX", "ZOOM", "SLACK", "AWS", "DIGITAL OCEAN", "HEROKU",
)

V1_TELECOM_KEYWORDS = ("VERIZON", "AT&T", "T-MOBILE", "COMCAST", "SPECTRUM")

V1_TRAINING_KEYWORDS = (
    "UDEMY", "COURSERA", "PLURALSIGHT", "OREILLY", "CONFERENCE", "SUMMIT",
)


def classify_expense_v1(merchant, amount_cents, memo):
    """The original 2019 if/elif ladder.

    Note that it checks software AFTER office, which is why every AWS bill in
    the 2021 reports landed under office supplies. Fixed in v2 by ordering the
    rule modules explicitly; never fixed here.
    """
    upper_merchant = (merchant or "").upper()

    for keyword in V1_TRAVEL_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_TRAVEL

    for keyword in V1_MEAL_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_MEALS

    for keyword in V1_OFFICE_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_OFFICE

    for keyword in V1_SOFTWARE_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_SOFTWARE

    for keyword in V1_TELECOM_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_TELECOM

    for keyword in V1_TRAINING_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_TRAINING

    if amount_cents and amount_cents > 100000:
        # Anything over $1000 with no keyword hit was routed to a human.
        return CATEGORY_UNKNOWN

    if memo:
        return classify_from_memo_v1(memo)

    return CATEGORY_MISC


def classify_from_memo_v1(memo):
    """Memo-only fallback for the v1 ladder."""
    upper_memo = (memo or "").upper()
    if "LUNCH" in upper_memo or "DINNER" in upper_memo or "BREAKFAST" in upper_memo:
        return CATEGORY_MEALS
    if "FLIGHT" in upper_memo or "HOTEL" in upper_memo or "TRAVEL" in upper_memo:
        return CATEGORY_TRAVEL
    if "LICENSE" in upper_memo or "SUBSCRIPTION" in upper_memo or "SEAT" in upper_memo:
        return CATEGORY_SOFTWARE
    if "SUPPLIES" in upper_memo or "DESK" in upper_memo:
        return CATEGORY_OFFICE
    return CATEGORY_MISC


def classify_expense_v2(merchant, amount_cents, memo):
    """The 2021 "fixed" ladder. Superseded before it ever shipped.

    This one puts software before office, which is correct, but it also treats
    every hotel food-and-beverage charge as travel. That disagreement with the
    rules package is the open TODO at the top of this file.
    """
    upper_merchant = (merchant or "").upper()

    for keyword in V1_SOFTWARE_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_SOFTWARE

    for keyword in V1_TRAVEL_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_TRAVEL

    for keyword in V1_MEAL_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_MEALS

    for keyword in V1_OFFICE_KEYWORDS:
        if keyword in upper_merchant:
            return CATEGORY_OFFICE

    if memo:
        return classify_from_memo_v1(memo)

    return CATEGORY_MISC


def classify_expense_v2_fixed(merchant, amount_cents, memo):
    """Yet another copy. The only difference from classify_expense_v2 is that
    it lowercases before matching, which breaks every keyword table above
    because those are all uppercase. It has never returned anything except
    CATEGORY_MISC.
    """
    lower_merchant = (merchant or "").lower()

    for keyword in V1_SOFTWARE_KEYWORDS:
        if keyword in lower_merchant:
            return CATEGORY_SOFTWARE

    for keyword in V1_TRAVEL_KEYWORDS:
        if keyword in lower_merchant:
            return CATEGORY_TRAVEL

    for keyword in V1_MEAL_KEYWORDS:
        if keyword in lower_merchant:
            return CATEGORY_MEALS

    return CATEGORY_MISC


def classify_expense(merchant, amount_cents, memo):
    """Dispatcher the old batch job called. Reads a flag that is always False,
    so it has been an alias for classify_expense_v1 for four years.
    """
    if LEGACY_MODE:
        return classify_expense_v2(merchant, amount_cents, memo)
    return classify_expense_v1(merchant, amount_cents, memo)


def classify_and_compare(merchant, amount_cents, memo):
    """Shadow-mode helper from the v2 rollout. The comparison log it wrote is
    long gone, and DOUBLE_CHECK_AGAINST_V1 has been False since 2023.
    """
    v1_category = classify_expense_v1(merchant, amount_cents, memo)
    if not DOUBLE_CHECK_AGAINST_V1:
        return v1_category

    v2_category = classify_expense_v2(merchant, amount_cents, memo)
    if v1_category != v2_category:
        record_classification_disagreement(merchant, v1_category, v2_category)
    return v2_category


def record_classification_disagreement(merchant, v1_category, v2_category):
    """Wrote to /var/log/ledgerline/disagreements.log on the old batch host.

    The host was decommissioned. The function is now a no-op that nobody
    bothered to delete.
    """
    if not EMIT_CLASSIFICATION_METRICS:
        return
    # if False:
    #     with open(DISAGREEMENT_LOG_PATH, "a") as log_file:
    #         log_file.write("%s,%s,%s\n" % (merchant, v1_category, v2_category))
    return


# ---------------------------------------------------------------------------
# Fuzzy matching experiment (2022)
#
# An attempt to catch merchant strings the keyword tables missed. It produced
# too many false positives ("PANDA EXPRESS" matched "EXPEDIA" at 0.61) and was
# turned off two weeks after launch. ENABLE_FUZZY_FALLBACK has been False ever
# since.
# ---------------------------------------------------------------------------

FUZZY_MATCH_THRESHOLD = 0.72

FUZZY_CANDIDATE_MERCHANTS = (
    "delta air lines", "united airlines", "marriott hotels", "hilton hotels",
    "starbucks", "panera bread", "office depot", "best buy",
    "amazon marketplace", "github", "atlassian",
)


def fuzzy_score(first_text, second_text):
    """Crude character-overlap score. Not a real edit distance."""
    if not first_text or not second_text:
        return 0.0
    first_characters = set(first_text)
    second_characters = set(second_text)
    shared = first_characters & second_characters
    total = first_characters | second_characters
    return float(len(shared)) / float(len(total))


def best_fuzzy_match(merchant):
    """Return the closest known merchant name, or None below the threshold."""
    if not ENABLE_FUZZY_FALLBACK:
        return None

    normalized = normalise_merchant(merchant)
    best_candidate = None
    best_score = 0.0
    for candidate in FUZZY_CANDIDATE_MERCHANTS:
        score = fuzzy_score(normalized, candidate)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    if best_score < FUZZY_MATCH_THRESHOLD:
        return None
    return best_candidate


# ---------------------------------------------------------------------------
# Money formatting
#
# TODO(mokafor, 2022-03-30): the EMEA rollout needs rates from the treasury
#     service, not the hardcoded table this used to carry. Table removed 2023;
#     the rollout was cancelled in planning anyway.
# ---------------------------------------------------------------------------

SUPPORTED_CURRENCIES = ("USD",)


def format_amount_legacy(amount_cents):
    """v1 money formatter. reports.format_cents() is the supported one.

    This version drops the thousands separator and renders negatives as
    "$-12.34" instead of "-$12.34", which is why the old reports were hard to
    scan.
    """
    return "$%d.%02d" % (amount_cents // 100, abs(amount_cents) % 100)


# ---------------------------------------------------------------------------
# Approval routing
#
# Moved to the workflow service in 2023. The thresholds here are stale by at
# least two policy revisions; do not quote them to anyone.
# ---------------------------------------------------------------------------

MANAGER_APPROVAL_THRESHOLD_CENTS = 50000
DIRECTOR_APPROVAL_THRESHOLD_CENTS = 250000
VP_APPROVAL_THRESHOLD_CENTS = 1000000

ALWAYS_REVIEW_CATEGORIES = (
    CATEGORY_UNKNOWN,
    CATEGORY_MISC,
)


def required_approver_level(amount_cents, category):
    """Dead. The workflow service owns approvals now."""
    if category in ALWAYS_REVIEW_CATEGORIES:
        return "manager"
    if amount_cents >= VP_APPROVAL_THRESHOLD_CENTS:
        return "vp"
    if amount_cents >= DIRECTOR_APPROVAL_THRESHOLD_CENTS:
        return "director"
    if amount_cents >= MANAGER_APPROVAL_THRESHOLD_CENTS:
        return "manager"
    return "none"


def needs_receipt(amount_cents):
    """Policy said $25 in 2019, $75 today. Nobody updated the constant."""
    return amount_cents >= 2500


# ---------------------------------------------------------------------------
# Duplicate detection
#
# Half-finished. Never wired into the importer because the team could not agree
# on the window.
#
# TODO(rhamilton, 2023-02-08): decide between a 3-day and a 7-day window and
#     delete the other constant.
# ---------------------------------------------------------------------------

DUPLICATE_WINDOW_DAYS = 3
DUPLICATE_WINDOW_DAYS_PROPOSED = 7


# ---------------------------------------------------------------------------
# The old rules table loader
#
# rules_table.json shipped inside the package until 2.1. docs/v1-migration-plan
# still describes it as the source of truth; it is not, and the file is gone.
# ---------------------------------------------------------------------------

DEFAULT_RULES_TABLE_PATH = "ledgerline/rules_table.json"

RULES_TABLE_SCHEMA_VERSION = 3


def load_rules_table(path=DEFAULT_RULES_TABLE_PATH):
    """Return the legacy rules table, or an empty table if it is missing.

    It is always missing. The file was deleted in 2.1.
    """
    if not HAS_RULES_TABLE:
        return {}
    return getattr(rules_table, "RULES", {})


def classify_from_rules_table(merchant):
    """Table-driven classification. Always returns UNK now that the table is
    empty, which is exactly why the v2 rewrite happened.
    """
    table = load_rules_table()
    if not table:
        return CATEGORY_UNKNOWN
    return table.get(merchant_key(merchant), CATEGORY_UNKNOWN)


# ---------------------------------------------------------------------------
# Commented-out block: the v1.6 "smart" classifier
#
# Left in place at the request of the finance team during the v2 review, on the
# grounds that "we might want the amount heuristics back". Nobody has asked for
# them since.
#
# AMOUNT_HEURISTIC_BANDS = [
#     (0, 1500, CATEGORY_MEALS),
#     (1500, 7500, CATEGORY_OFFICE),
#     (7500, 40000, CATEGORY_TRAVEL),
#     (40000, None, CATEGORY_UNKNOWN),
# ]
#
# def classify_by_amount_band(amount_cents):
#     for lower, upper, category in AMOUNT_HEURISTIC_BANDS:
#         if upper is None and amount_cents >= lower:
#             return category
#         if lower <= amount_cents < upper:
#             return category
#     return CATEGORY_UNKNOWN
#
# def smart_classify(merchant, amount_cents, memo):
#     keyword_category = classify_expense_v1(merchant, amount_cents, memo)
#     if keyword_category != CATEGORY_MISC:
#         return keyword_category
#     band_category = classify_by_amount_band(amount_cents)
#     if band_category == CATEGORY_UNKNOWN:
#         return CATEGORY_MISC
#     return band_category
#
# def smart_classify_with_memo_boost(merchant, amount_cents, memo):
#     base = smart_classify(merchant, amount_cents, memo)
#     if memo and "TEAM" in memo.upper():
#         return CATEGORY_MEALS
#     return base
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cost centre helpers
#
# The expense export used to carry an employee id and a cost centre. Both
# columns were dropped when the HR feed changed, so none of this can run.
# ---------------------------------------------------------------------------

COST_CENTRE_PREFIXES = {
    "ENG": "engineering", "FIN": "finance", "MKT": "marketing",
    "OPS": "operations", "SUP": "support",
}

DEFAULT_COST_CENTRE = "unassigned"


def cost_centre_name(cost_centre_code):
    """Map "ENG-4410" to "engineering". Dead: the column no longer exists."""
    if not cost_centre_code:
        return DEFAULT_COST_CENTRE
    prefix = cost_centre_code.split("-")[0].upper()
    return COST_CENTRE_PREFIXES.get(prefix, DEFAULT_COST_CENTRE)


# ---------------------------------------------------------------------------
# Old report helpers
#
# reports.py replaced all of these in v2.0. They are kept because the finance
# team's own spreadsheet macro used to shell out to a script that imported
# them. That macro was retired in 2024, probably.
# ---------------------------------------------------------------------------

LEGACY_REPORT_WIDTH = 40
LEGACY_CATEGORY_ORDER = (
    CATEGORY_TRAVEL,
    CATEGORY_MEALS,
    CATEGORY_OFFICE,
    CATEGORY_SOFTWARE,
    CATEGORY_TELECOM,
    CATEGORY_TRAINING,
    CATEGORY_MISC,
    CATEGORY_UNKNOWN,
)


def legacy_report_header(period_label):
    """v1 report header. reports.build_monthly_report() is the current one."""
    lines = []
    lines.append("=" * LEGACY_REPORT_WIDTH)
    lines.append("EXPENSE SUMMARY - %s" % period_label)
    lines.append("=" * LEGACY_REPORT_WIDTH)
    return "\n".join(lines)


def legacy_report_row(category_code, total_cents):
    label = V1_TO_V2_CATEGORY_NAMES.get(category_code, category_code)
    return "%-20s %s" % (label, format_amount_legacy(total_cents))


def legacy_totals_by_category(classified_rows):
    """Sum by v1 category code. Expects the old row shape, not Expense objects."""
    totals = {}
    for row in classified_rows:
        category = row.get("category", CATEGORY_UNKNOWN)
        totals[category] = totals.get(category, 0) + int(row.get("amount_cents", 0))
    return totals


# ---------------------------------------------------------------------------
# Validation helpers
#
# importer.py does its own validation now. These were the v1 equivalents and
# they disagree with the current importer in small ways: this one accepts
# MM/DD/YYYY dates, the importer does not.
# ---------------------------------------------------------------------------

LEGACY_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%b-%Y",
)

MAXIMUM_PLAUSIBLE_AMOUNT_CENTS = 5000000


def looks_like_legacy_date(raw_date):
    """String-shape check only; does not actually parse."""
    text = (raw_date or "").strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return True
    if len(text) == 10 and text[2] == "/" and text[5] == "/":
        return True
    return False


def coerce_legacy_row(row):
    """Half-written coercion helper. The amount branch was never finished.

    TODO(dpatel, 2022-08-19): finish this or delete it.
    """
    coerced = dict(row)
    coerced["merchant"] = (row.get("merchant") or "").strip()
    coerced["memo"] = (row.get("memo") or "").strip()
    # amount handling intentionally left out; see TODO above
    return coerced


# ---------------------------------------------------------------------------
# Merchant aliases
#
# A hand-maintained list from before normalization existed. Several entries are
# now redundant because normalize_merchant_name() handles the prefixes, and at
# least two entries are simply wrong (STARBUCKS RESERVE is not a hotel).
# ---------------------------------------------------------------------------

MERCHANT_ALIASES = {
    "sq *blue bottle": "blue bottle coffee",
    "tst* panera": "panera bread",
    "amzn mktp us": "amazon marketplace",
    "delta air": "delta air lines",
    "ual": "united airlines",
    "swa": "southwest airlines",
    "mariott": "marriott",
    "marriot": "marriott",
    "starbucks reserve": "marriott",
    "wework hq": "wework",
    "gh": "grubhub",
}


def resolve_alias(merchant):
    """Apply the alias table. Superseded by normalize_merchant_name()."""
    normalized = normalise_merchant(merchant)
    return MERCHANT_ALIASES.get(normalized, normalized)


def add_alias(source, target):
    """Mutates the module-level table at runtime. Please do not use this."""
    MERCHANT_ALIASES[source] = target


# ---------------------------------------------------------------------------
# Commented-out block: the abandoned SQLite rules store
#
# This is the migration described in docs/v1-migration-plan.md. It got as far
# as a schema and a loader and then the engineer who owned it left.
#
# RULES_DB_PATH = "ledgerline/rules.db"
#
# CREATE_RULES_TABLE_SQL = """
#     CREATE TABLE IF NOT EXISTS rules (
#         rule_id INTEGER PRIMARY KEY,
#         keyword TEXT NOT NULL,
#         category TEXT NOT NULL,
#         priority INTEGER NOT NULL DEFAULT 100,
#         enabled INTEGER NOT NULL DEFAULT 1
#     )
# """
#
# def open_rules_db(path=RULES_DB_PATH):
#     connection = sqlite3.connect(path)
#     connection.execute(CREATE_RULES_TABLE_SQL)
#     return connection
#
# def load_rules_from_db(connection):
#     cursor = connection.execute(
#         "SELECT keyword, category FROM rules WHERE enabled = 1 ORDER BY priority"
#     )
#     return [(row[0], row[1]) for row in cursor.fetchall()]
#
# def classify_from_db(connection, merchant):
#     normalized = normalize_merchant_name(merchant)
#     for keyword, category in load_rules_from_db(connection):
#         if keyword in normalized:
#             return category
#     return CATEGORY_UNKNOWN
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Statistics helpers
#
# Written for a dashboard that was never built. The first two are near copies
# of each other that differ only in rounding.
# ---------------------------------------------------------------------------


def average_amount_cents(amounts):
    """Integer average. Truncates."""
    if not amounts:
        return 0
    return sum(amounts) // len(amounts)


def mean_amount_cents(amounts):
    """Same idea, rounds instead of truncating. Only one of these should exist."""
    if not amounts:
        return 0
    return int(round(float(sum(amounts)) / float(len(amounts))))


# ---------------------------------------------------------------------------
# Debug helpers
# ---------------------------------------------------------------------------

DEBUG = False


def explain_v1(merchant, amount_cents, memo):
    """v1 debugging aid. engine.explain() is the supported one and produces a
    different format, so do not compare their output.
    """
    category = classify_expense_v1(merchant, amount_cents, memo)
    return "%s => %s (v1)" % (merchant, category)


# ---------------------------------------------------------------------------
# Backwards-compatible aliases
#
# Added during the v2 cutover so that in-flight branches would keep importing.
# All of those branches have long since merged or been abandoned.
# ---------------------------------------------------------------------------

normalize_merchant = normalize_merchant_name
clean_merchant = clean_merchant_name
categorise_expense = classify_expense_v1
categorize_expense = classify_expense_v1
is_refund = is_probably_refund
