import django.test

import blockinclude.string


class TestHasQuotes(django.test.SimpleTestCase):
    def test_single_quotes(self) -> None:
        self.assertTrue(blockinclude.string.has_quotes('"Double quotes"'))

    def test_double_quotes(self) -> None:
        self.assertTrue(blockinclude.string.has_quotes("'Single quotes'"))

    def test_mixed_quotes(self) -> None:
        self.assertFalse(blockinclude.string.has_quotes("'Mixed quotes\""))

    def test_unquoted_quotes(self) -> None:
        self.assertFalse(blockinclude.string.has_quotes("No quotes"))
