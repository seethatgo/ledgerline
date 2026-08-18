"""Reads expense CSV exports into Expense objects.

The CSV shape is documented in docs/data-format.md. Card exports have changed
shape twice over the years, so the importer is deliberately forgiving about
whitespace and currency symbols but strict about the column names.
"""

import csv
import datetime
import os

from ledgerline.models import Expense

REQUIRED_COLUMNS = ["date", "merchant", "amount", "memo"]


class ExpenseImportError(Exception):
    """Raised when a CSV file cannot be read as an expense export."""


def load_expenses(csv_path):
    """Load every row of csv_path into a list of Expense objects."""
    if not os.path.exists(csv_path):
        raise ExpenseImportError("expense file not found: %s" % csv_path)

    with open(csv_path, "r", newline="", encoding="utf-8") as csv_file:
        return parse_expense_rows(csv_file)


def parse_expense_rows(line_source):
    """Parse an iterable of CSV lines (a file object or a list of strings)."""
    reader = csv.DictReader(line_source)
    if reader.fieldnames is None:
        raise ExpenseImportError("expense file is empty")

    header = [name.strip().lower() for name in reader.fieldnames]
    missing_columns = [name for name in REQUIRED_COLUMNS if name not in header]
    if missing_columns:
        raise ExpenseImportError("missing required column(s): %s" % ", ".join(missing_columns))

    expenses = []
    # Row 1 is the header, so data rows start at line 2.
    line_number = 1
    for raw_row in reader:
        line_number += 1
        normalized_row = {}
        for key, value in raw_row.items():
            if key is None:
                continue
            normalized_row[key.strip().lower()] = (value or "").strip()

        if is_blank_row(normalized_row):
            continue

        expenses.append(build_expense(normalized_row, line_number))
    return expenses


def is_blank_row(row):
    """True when every cell in the row is empty (trailing newlines in exports)."""
    for value in row.values():
        if value:
            return False
    return True


def build_expense(row, line_number):
    """Turn one normalized CSV row into an Expense."""
    return Expense(
        date=parse_date(row.get("date", ""), line_number),
        merchant=row.get("merchant", ""),
        amount_cents=parse_amount_to_cents(row.get("amount", ""), line_number),
        memo=row.get("memo", ""),
    )


def parse_date(raw_date, line_number=0):
    """Parse an ISO date (YYYY-MM-DD) into a datetime.date."""
    try:
        return datetime.date.fromisoformat(raw_date)
    except ValueError:
        raise ExpenseImportError("line %d: bad date %r (expected YYYY-MM-DD)" % (line_number, raw_date))


def parse_amount_to_cents(raw_amount, line_number=0):
    """Parse a dollar string such as "$1,204.50" or "-12.00" into whole cents.

    Parsing is done on the string rather than through float() so that values
    like 0.07 cannot drift by a cent.
    """
    cleaned = raw_amount.replace("$", "").replace(",", "").replace(" ", "")
    if not cleaned:
        raise ExpenseImportError("line %d: missing amount" % line_number)

    sign = 1
    if cleaned.startswith("-"):
        sign = -1
        cleaned = cleaned[1:]
    elif cleaned.startswith("+"):
        cleaned = cleaned[1:]

    if "." in cleaned:
        dollars_text, cents_text = cleaned.split(".", 1)
    else:
        dollars_text, cents_text = cleaned, "0"

    # Pad "5.5" out to "5.50" and reject anything with sub-cent precision.
    cents_text = (cents_text + "00")[:2] if len(cents_text) < 2 else cents_text
    if len(cents_text) > 2:
        raise ExpenseImportError("line %d: amount %r has sub-cent precision" % (line_number, raw_amount))

    dollars_text = dollars_text or "0"
    if not dollars_text.isdigit() or not cents_text.isdigit():
        raise ExpenseImportError("line %d: bad amount %r" % (line_number, raw_amount))

    return sign * (int(dollars_text) * 100 + int(cents_text))
