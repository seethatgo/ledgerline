"""Core value objects for LedgerLine.

An Expense is intentionally dumb: it holds data and does no categorization of
its own. All classification lives in ledgerline/engine.py and ledgerline/rules/.
"""

UNCATEGORIZED = "uncategorized"


class Expense:
    """One row from an expense export."""

    def __init__(self, date, merchant, amount_cents, memo="", category=UNCATEGORIZED):
        # date is a datetime.date; the importer is responsible for parsing it.
        self.date = date
        self.merchant = merchant
        # Amounts are stored as whole cents so we never do float math on money.
        self.amount_cents = amount_cents
        self.memo = memo
        self.category = category

    @property
    def month_key(self):
        """Sortable "YYYY-MM" string used to group expenses into report periods."""
        return "%04d-%02d" % (self.date.year, self.date.month)

    def with_category(self, category):
        """Return a copy of this expense carrying a new category.

        Categorization returns new objects instead of mutating in place so a
        caller can always compare "before" and "after" lists.
        """
        return Expense(
            date=self.date,
            merchant=self.merchant,
            amount_cents=self.amount_cents,
            memo=self.memo,
            category=category,
        )

    def __eq__(self, other):
        if not isinstance(other, Expense):
            return NotImplemented
        return (
            self.date == other.date
            and self.merchant == other.merchant
            and self.amount_cents == other.amount_cents
            and self.memo == other.memo
            and self.category == other.category
        )

    def __repr__(self):
        return "Expense(date=%r, merchant=%r, amount_cents=%r, category=%r)" % (
            self.date,
            self.merchant,
            self.amount_cents,
            self.category,
        )


class CategoryTotal:
    """Aggregated spend for a single category within one report period."""

    def __init__(self, category, total_cents, expense_count):
        self.category = category
        self.total_cents = total_cents
        self.expense_count = expense_count

    def __eq__(self, other):
        if not isinstance(other, CategoryTotal):
            return NotImplemented
        return (
            self.category == other.category
            and self.total_cents == other.total_cents
            and self.expense_count == other.expense_count
        )

    def __repr__(self):
        return "CategoryTotal(category=%r, total_cents=%r, expense_count=%r)" % (
            self.category,
            self.total_cents,
            self.expense_count,
        )
