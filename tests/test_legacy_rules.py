"""Tests for the two helpers in legacy_rules.py that are still live.

Everything else in that module is historical and deliberately untested.
"""

import unittest

from ledgerline.legacy_rules import is_probably_refund, normalize_merchant_name


class NormalizeMerchantNameTests(unittest.TestCase):
    def test_strips_processor_prefixes(self):
        self.assertEqual(normalize_merchant_name("SQ *BLUE BOTTLE COFFEE"), "blue bottle coffee")
        self.assertEqual(normalize_merchant_name("TST* PANERA BREAD #2214"), "panera bread")

    def test_replaces_punctuation_with_spaces(self):
        self.assertEqual(normalize_merchant_name("APPLE.COM/BILL"), "apple com bill")

    def test_drops_long_numeric_tokens(self):
        self.assertEqual(normalize_merchant_name("DELTA AIR 0062378891234"), "delta air")

    def test_keeps_short_numbers_that_are_part_of_a_name(self):
        self.assertEqual(normalize_merchant_name("7-ELEVEN 33221"), "7 eleven")

    def test_lowercases_and_collapses_whitespace(self):
        self.assertEqual(normalize_merchant_name("  UBER   *EATS  SF "), "uber eats sf")

    def test_handles_empty_input(self):
        self.assertEqual(normalize_merchant_name(""), "")
        self.assertEqual(normalize_merchant_name(None), "")


class IsProbablyRefundTests(unittest.TestCase):
    def test_only_negative_amounts_are_refunds(self):
        self.assertTrue(is_probably_refund(-14999))
        self.assertFalse(is_probably_refund(0))
        self.assertFalse(is_probably_refund(9200))


if __name__ == "__main__":
    unittest.main()
