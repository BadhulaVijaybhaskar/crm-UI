# Copyright (c) 2026, Astra and contributors
import hashlib
import unittest


class TestApiKeyHash(unittest.TestCase):
	def test_sha256_hex(self):
		raw = "crm_test_key_value"
		expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
		self.assertEqual(len(expected), 64)
		self.assertNotEqual(expected, raw)


if __name__ == "__main__":
	unittest.main()
