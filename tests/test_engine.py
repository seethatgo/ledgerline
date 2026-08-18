import datetime
import unittest

from ledgerline.engine import RULE_MODULES, categorize, categorize_all, explain
from ledgerline.models import Expense


def make_expense(merchant, amount_cents=1000, memo=""):
    return Expense(
        date=datetime.date(2026, 7, 1),
        merchant=merchant,
        amount_cents=amount_cents,
        memo=memo,
    )


class EvaluationOrderTests(unittest.TestCase):
    def test_rule_modules_are_in_the_documented_order(self):
        module_names = [module.__name__.rsplit(".", 1)[-1] for module in RULE_MODULES]
        self.assertEqual(module_names, ["travel", "meals", "office", "subscriptions"])

    def test_first_match_wins_when_two_modules_could_match(self):
        # "airport" is a travel keyword and "starbucks" is a meals keyword.
        # Travel is evaluated first, so an airport coffee shop lands in travel.
        self.assertEqual(categorize(make_expense("SQ *STARBUCKS AIRPORT T2")), "travel")

    def test_excluded_keyword_lets_a_later_module_match(self):
        self.assertEqual(categorize(make_expense("UBER *EATS SAN FRANCISCO")), "meals")


class CategorizeTests(unittest.TestCase):
    def test_one_representative_merchant_per_category(self):
        self.assertEqual(categorize(make_expense("DELTA AIR 0062378891234")), "travel")
        self.assertEqual(categorize(make_expense("TST* PANERA BREAD #2214")), "meals")
        self.assertEqual(categorize(make_expense("STAPLES 00921")), "office")
        self.assertEqual(categorize(make_expense("GITHUB INC")), "subscriptions")

    def test_unknown_merchant_falls_back_to_uncategorized(self):
        self.assertEqual(categorize(make_expense("SHELL OIL 57219004")), "uncategorized")

    def test_memo_is_used_when_the_merchant_does_not_match(self):
        expense = make_expense("THE CORNER SPOT", memo="team lunch")
        self.assertEqual(categorize(expense), "meals")

    def test_refund_short_circuits_before_the_rule_modules(self):
        # The merchant would otherwise match travel.
        expense = make_expense("DELTA AIR REFUND 0062378", amount_cents=-41230)
        self.assertEqual(categorize(expense), "refund")


class CategorizeAllTests(unittest.TestCase):
    def test_returns_new_objects_and_leaves_the_input_alone(self):
        original = make_expense("GITHUB INC")
        categorized = categorize_all([original])
        self.assertEqual(categorized[0].category, "subscriptions")
        self.assertEqual(original.category, "uncategorized")


class ExplainTests(unittest.TestCase):
    def test_explanation_names_the_category_the_module_and_the_normalized_name(self):
        explanation = explain(make_expense("TST* PANERA BREAD #2214"))
        self.assertIn("meals", explanation)
        self.assertIn("panera bread", explanation)


if __name__ == "__main__":
    unittest.main()
