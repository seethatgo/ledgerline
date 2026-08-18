import datetime
import unittest

from ledgerline.models import Expense
from ledgerline.rules import meals


def make_expense(merchant, memo=""):
    return Expense(
        date=datetime.date(2026, 7, 1),
        merchant=merchant,
        amount_cents=10000,
        memo=memo,
    )


class MealsRuleTests(unittest.TestCase):
    def test_category_name(self):
        self.assertEqual(meals.CATEGORY_NAME, "meals")

    def test_matches_restaurants_coffee_and_delivery(self):
        self.assertTrue(meals.matches(make_expense("TST* PANERA BREAD #2214")))
        self.assertTrue(meals.matches(make_expense("SQ *BLUE BOTTLE COFFEE")))
        self.assertTrue(meals.matches(make_expense("DOORDASH*SWEETGREEN")))

    def test_matches_on_memo_when_the_merchant_is_unknown(self):
        self.assertTrue(meals.matches(make_expense("THE CORNER SPOT", memo="team lunch")))

    def test_also_matches_an_airport_coffee_shop(self):
        # Travel matches this one too, and travel is evaluated first, so the
        # engine categorizes it as travel. See tests/test_engine.py.
        self.assertTrue(meals.matches(make_expense("SQ *STARBUCKS AIRPORT T2")))

    def test_does_not_match_a_subscription_merchant(self):
        self.assertFalse(meals.matches(make_expense("GITHUB INC")))


if __name__ == "__main__":
    unittest.main()
