import datetime
import os
import unittest

from ledgerline.importer import (
    ExpenseImportError,
    load_expenses,
    parse_amount_to_cents,
    parse_date,
    parse_expense_rows,
)

DATA_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

HEADER = "date,merchant,amount,memo"


class ParseAmountTests(unittest.TestCase):
    def test_parses_dollar_strings_into_cents(self):
        self.assertEqual(parse_amount_to_cents("48.90"), 4890)
        self.assertEqual(parse_amount_to_cents("$1,240.11"), 124011)
        self.assertEqual(parse_amount_to_cents("96"), 9600)
        self.assertEqual(parse_amount_to_cents("5.5"), 550)

    def test_parses_negative_amount_as_credit(self):
        self.assertEqual(parse_amount_to_cents("-412.30"), -41230)

    def test_rejects_unusable_amounts(self):
        for bad_amount in ("12.3456", "", "twelve dollars"):
            with self.assertRaises(ExpenseImportError):
                parse_amount_to_cents(bad_amount)


class ParseDateTests(unittest.TestCase):
    def test_parses_iso_date(self):
        self.assertEqual(parse_date("2026-07-14"), datetime.date(2026, 7, 14))

    def test_rejects_us_style_date(self):
        with self.assertRaises(ExpenseImportError):
            parse_date("07/14/2026")


class ParseRowsTests(unittest.TestCase):
    def test_reads_a_row_into_an_expense(self):
        lines = [HEADER, "2026-07-01,GITHUB INC,92.00,team seats"]
        expenses = parse_expense_rows(lines)
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0].merchant, "GITHUB INC")
        self.assertEqual(expenses[0].amount_cents, 9200)
        self.assertEqual(expenses[0].memo, "team seats")

    def test_skips_blank_rows_and_allows_an_empty_memo(self):
        lines = [HEADER, "2026-07-01,PEETS COFFEE 3391,12.40,", ",,,", ""]
        expenses = parse_expense_rows(lines)
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0].memo, "")

    def test_reports_missing_columns(self):
        lines = ["date,merchant", "2026-07-01,GITHUB INC"]
        with self.assertRaises(ExpenseImportError) as raised:
            parse_expense_rows(lines)
        self.assertIn("amount", str(raised.exception))

    def test_reports_the_line_number_of_a_bad_row(self):
        lines = [HEADER, "2026-07-01,GITHUB INC,92.00,ok", "nope,STAPLES,10.00,"]
        with self.assertRaises(ExpenseImportError) as raised:
            parse_expense_rows(lines)
        self.assertIn("line 3", str(raised.exception))


class LoadExpensesTests(unittest.TestCase):
    def test_loads_the_july_sample_file(self):
        path = os.path.join(DATA_DIRECTORY, "expenses_2026_07.csv")
        expenses = load_expenses(path)
        self.assertEqual(len(expenses), 62)
        self.assertTrue(all(expense.date.month == 7 for expense in expenses))

    def test_missing_file_raises(self):
        with self.assertRaises(ExpenseImportError):
            load_expenses(os.path.join(DATA_DIRECTORY, "no_such_file.csv"))


if __name__ == "__main__":
    unittest.main()
