"""Monthly summary reporting.

Finance pastes this output straight into the month-end close ticket, so the
column layout is fixed. Do not reformat without asking the Finance Platform
team first.
"""

from ledgerline.models import UNCATEGORIZED, CategoryTotal

REPORT_WIDTH = 52
CATEGORY_COLUMN_WIDTH = 20


def group_by_month(expenses):
    """Group expenses into a dict of "YYYY-MM" -> list of expenses."""
    grouped = {}
    for expense in expenses:
        grouped.setdefault(expense.month_key, []).append(expense)
    return grouped


def summarize_by_category(expenses):
    """Total spend per category, largest total first.

    Ties are broken alphabetically so the report is stable between runs.
    """
    totals_by_category = {}
    counts_by_category = {}
    for expense in expenses:
        category = expense.category
        totals_by_category[category] = totals_by_category.get(category, 0) + expense.amount_cents
        counts_by_category[category] = counts_by_category.get(category, 0) + 1

    summaries = []
    for category in totals_by_category:
        summaries.append(
            CategoryTotal(
                category=category,
                total_cents=totals_by_category[category],
                expense_count=counts_by_category[category],
            )
        )
    summaries.sort(key=lambda summary: (-summary.total_cents, summary.category))
    return summaries


def format_cents(amount_cents):
    """Render whole cents as a dollar string, e.g. -12345 -> "-$123.45"."""
    sign = "-" if amount_cents < 0 else ""
    absolute_cents = abs(amount_cents)
    return "%s$%s.%02d" % (sign, "{:,}".format(absolute_cents // 100), absolute_cents % 100)


def build_monthly_report(expenses, month_key):
    """Return the plain-text report for one month as a single string."""
    lines = []
    lines.append("LedgerLine monthly expense report")
    lines.append("Period: %s" % month_key)
    lines.append("-" * REPORT_WIDTH)

    if not expenses:
        lines.append("No expenses recorded for this period.")
        lines.append("-" * REPORT_WIDTH)
        return "\n".join(lines)

    for summary in summarize_by_category(expenses):
        lines.append(format_summary_line(summary))

    lines.append("-" * REPORT_WIDTH)
    total_cents = sum(expense.amount_cents for expense in expenses)
    lines.append(format_total_line(total_cents, len(expenses)))

    review_lines = build_review_section(expenses)
    if review_lines:
        lines.append("")
        lines.extend(review_lines)

    return "\n".join(lines)


def format_summary_line(summary):
    return "%s %12s  (%d)" % (
        summary.category.ljust(CATEGORY_COLUMN_WIDTH),
        format_cents(summary.total_cents),
        summary.expense_count,
    )


def format_total_line(total_cents, expense_count):
    return "%s %12s  (%d)" % (
        "TOTAL".ljust(CATEGORY_COLUMN_WIDTH),
        format_cents(total_cents),
        expense_count,
    )


def build_review_section(expenses):
    """List the merchants that fell through every rule module.

    An empty list means nothing needs review, and the caller omits the section.
    """
    unmatched_merchants = []
    for expense in expenses:
        if expense.category == UNCATEGORIZED and expense.merchant not in unmatched_merchants:
            unmatched_merchants.append(expense.merchant)

    if not unmatched_merchants:
        return []

    lines = ["Needs review (%d merchant(s) matched no rule):" % len(unmatched_merchants)]
    for merchant in sorted(unmatched_merchants):
        lines.append("  - %s" % merchant)
    return lines


def build_full_report(expenses):
    """Report every month present in the data, oldest period first."""
    grouped = group_by_month(expenses)
    sections = []
    for month_key in sorted(grouped):
        sections.append(build_monthly_report(grouped[month_key], month_key))
    if not sections:
        return build_monthly_report([], "n/a")
    return "\n\n".join(sections)
