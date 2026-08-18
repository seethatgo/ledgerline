import datetime
import unittest

from ledgerline.models import Expense
from ledgerline.rules import travel


def make_expense(merchant, memo=""):
    return Expense(
        date=datetime.date(2026, 7, 1),
        merchant=merchant,
        amount_cents=10000,
        memo=memo,
    )


class TravelRuleTests(unittest.TestCase):
    def test_category_name(self):
        self.assertEqual(travel.CATEGORY_NAME, "travel")

    def test_matches_flights_hotels_rentals_and_rideshare(self):
        self.assertTrue(travel.matches(make_expense("DELTA AIR 0062378891234")))
        self.assertTrue(travel.matches(make_expense("MARRIOTT SEATTLE WATERFRONT")))
        self.assertTrue(travel.matches(make_expense("HERTZ RENT A CAR")))
        self.assertTrue(travel.matches(make_expense("UBER *TRIP HELP.UBER.COM")))

    def test_does_not_match_food_delivery_from_the_same_merchant_prefix(self):
        self.assertFalse(travel.matches(make_expense("UBER *EATS SAN FRANCISCO")))

    def test_matches_on_memo_when_the_merchant_is_unknown(self):
        self.assertTrue(travel.matches(make_expense("PORTLAND CITY LODGE", memo="hotel stay")))

    def test_does_not_match_an_office_merchant(self):
        self.assertFalse(travel.matches(make_expense("STAPLES 00921")))


if __name__ == "__main__":
    unittest.main()
