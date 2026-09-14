from django.test import SimpleTestCase

from apis.notification.notification_utils import _normalize_optional_int


class NormalizeOptionalIntTest(SimpleTestCase):

    def test_integer_stays_integer(self):
        result = _normalize_optional_int(5)

        self.assertEqual(result, 5)

    def test_numeric_string_becomes_integer(self):
        result = _normalize_optional_int("5")

        self.assertEqual(result, 5)

    def test_none_returns_none(self):
        result = _normalize_optional_int(None)

        self.assertIsNone(result)

    def test_invalid_string_returns_none(self):
        result = _normalize_optional_int("abc")

        self.assertIsNone(result)