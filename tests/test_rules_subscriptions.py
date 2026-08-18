import datetime
import unittest

from ledgerline.models import Expense
from ledgerline.rules import subscriptions


def make_expense(merchant, memo=""):
    return Expense(
        date=datetime.date(2026, 7, 1),
        merchant=merchant,
        amount_cents=10000,
        memo=memo,
    )


class SubscriptionsRuleTests(unittest.TestCase):
    def test_category_name(self):
        self.assertEqual(subscriptions.CATEGORY_NAME, "subscriptions")

    def test_matches_tooling_cloud_and_punctuated_merchants(self):
        self.assertTrue(subscriptions.matches(make_expense("GITHUB INC")))
        self.assertTrue(subscriptions.matches(make_expense("AMAZON WEB SERVICES")))
        self.assertTrue(subscriptions.matches(make_expense("APPLE.COM/BILL")))

    def test_matches_on_memo_when_the_merchant_is_unknown(self):
        self.assertTrue(subscriptions.matches(make_expense("PROJECTLY", memo="annual license")))

    def test_does_not_match_an_unknown_saas_vendor(self):
        # LinkedIn Premium is a real recurring charge that no rule covers yet.
        self.assertFalse(subscriptions.matches(make_expense("LINKEDIN PREMIUM")))

    def test_does_not_match_an_office_merchant(self):
        self.assertFalse(subscriptions.matches(make_expense("STAPLES 00921")))


if __name__ == "__main__":
    unittest.main()
