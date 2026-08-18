import datetime
import unittest

from ledgerline.models import Expense
from ledgerline.rules import office


def make_expense(merchant, memo=""):
    return Expense(
        date=datetime.date(2026, 7, 1),
        merchant=merchant,
        amount_cents=10000,
        memo=memo,
    )


class OfficeRuleTests(unittest.TestCase):
    def test_category_name(self):
        self.assertEqual(office.CATEGORY_NAME, "office")

    def test_matches_supplies_marketplace_orders_and_coworking(self):
        self.assertTrue(office.matches(make_expense("STAPLES 00921")))
        self.assertTrue(office.matches(make_expense("AMZN MKTP US*2X3AB9QQ1")))
        self.assertTrue(office.matches(make_expense("WEWORK 154 GRAND ST")))

    def test_does_not_match_cloud_infrastructure(self):
        self.assertFalse(office.matches(make_expense("AMAZON WEB SERVICES")))

    def test_matches_on_memo_when_the_merchant_is_unknown(self):
        self.assertTrue(office.matches(make_expense("PENINSULA SUPPLY CO", memo="office supplies")))

    def test_does_not_match_a_travel_merchant(self):
        self.assertFalse(office.matches(make_expense("DELTA AIR 0062378891234")))


if __name__ == "__main__":
    unittest.main()
