"""Command line entry point for the monthly expense report.

    python3 run_report.py data/expenses_2026_07.csv
    python3 run_report.py data/expenses_2026_07.csv --explain
"""

import sys

from ledgerline.engine import categorize_all, explain
from ledgerline.importer import ExpenseImportError, load_expenses
from ledgerline.reports import build_full_report

USAGE = "usage: python3 run_report.py <expenses.csv> [--explain]"


def main(argv):
    arguments = list(argv)
    show_explanations = "--explain" in arguments
    if show_explanations:
        arguments.remove("--explain")

    if len(arguments) != 1:
        print(USAGE)
        return 2

    try:
        expenses = load_expenses(arguments[0])
    except ExpenseImportError as error:
        print("error: %s" % error)
        return 1

    categorized_expenses = categorize_all(expenses)

    if show_explanations:
        for expense in categorized_expenses:
            print(explain(expense))
        print("")

    print(build_full_report(categorized_expenses))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
