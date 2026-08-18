import datetime
import unittest

from ledgerline.models import Expense
from ledgerline.reports import (
    build_full_report,
    build_monthly_report,
    format_cents,
    group_by_month,
    summarize_by_category,
)


def make_expense(day, merchant, amount_cents, category, month=7):
    return Expense(
        date=datetime.date(2026, month, day),
        merchant=merchant,
        amount_cents=amount_cents,
        memo="",
        category=category,
    )


SAMPLE_EXPENSES = [
    make_expense(1, "GITHUB INC", 9200, "subscriptions"),
    make_expense(2, "DELTA AIR 0062378891234", 52160, "travel"),
    make_expense(3, "TST* PANERA BREAD #2214", 4890, "meals"),
    make_expense(4, "STAPLES 00921", 3825, "office"),
    make_expense(5, "SHELL OIL 57219004", 6475, "uncategorized"),
]


class FormatCentsTests(unittest.TestCase):
    def test_formats_amounts_as_dollars(self):
        self.assertEqual(format_cents(4890), "$48.90")
        self.assertEqual(format_cents(124011), "$1,240.11")
        self.assertEqual(format_cents(0), "$0.00")

    def test_puts_the_sign_before_the_dollar_symbol(self):
        self.assertEqual(format_cents(-14999), "-$149.99")


class SummarizeTests(unittest.TestCase):
    def test_totals_and_counts_per_category(self):
        expenses = [
            make_expense(1, "GITHUB INC", 9200, "subscriptions"),
            make_expense(2, "SLACK TECHNOLOGIES", 24000, "subscriptions"),
        ]
        summaries = summarize_by_category(expenses)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0].total_cents, 33200)
        self.assertEqual(summaries[0].expense_count, 2)

    def test_orders_by_total_descending_then_alphabetically(self):
        self.assertEqual(summarize_by_category(SAMPLE_EXPENSES)[0].category, "travel")
        tied_expenses = [
            make_expense(1, "ONE", 1000, "office"),
            make_expense(2, "TWO", 1000, "meals"),
        ]
        categories = [summary.category for summary in summarize_by_category(tied_expenses)]
        self.assertEqual(categories, ["meals", "office"])


class GroupByMonthTests(unittest.TestCase):
    def test_groups_expenses_into_periods(self):
        expenses = [
            make_expense(1, "GITHUB INC", 9200, "subscriptions", month=6),
            make_expense(1, "GITHUB INC", 9200, "subscriptions", month=7),
            make_expense(2, "SLACK TECHNOLOGIES", 24000, "subscriptions", month=7),
        ]
        grouped = group_by_month(expenses)
        self.assertEqual(sorted(grouped), ["2026-06", "2026-07"])
        self.assertEqual(len(grouped["2026-07"]), 2)


class MonthlyReportTests(unittest.TestCase):
    def test_report_has_a_header_and_a_total(self):
        report = build_monthly_report(SAMPLE_EXPENSES, "2026-07")
        self.assertIn("Period: 2026-07", report)
        self.assertIn("TOTAL", report)
        self.assertIn("$765.50", report)

    def test_report_lists_unmatched_merchants_for_review(self):
        report = build_monthly_report(SAMPLE_EXPENSES, "2026-07")
        self.assertIn("Needs review", report)
        self.assertIn("SHELL OIL 57219004", report)

    def test_review_section_is_omitted_when_everything_matched(self):
        expenses = [make_expense(1, "GITHUB INC", 9200, "subscriptions")]
        self.assertNotIn("Needs review", build_monthly_report(expenses, "2026-07"))

    def test_full_report_prints_one_section_per_month_oldest_first(self):
        expenses = [
            make_expense(1, "GITHUB INC", 9200, "subscriptions", month=6),
            make_expense(1, "GITHUB INC", 9200, "subscriptions", month=7),
        ]
        report = build_full_report(expenses)
        self.assertIn("Period: 2026-06", report)
        self.assertLess(report.index("2026-06"), report.index("2026-07"))


if __name__ == "__main__":
    unittest.main()
