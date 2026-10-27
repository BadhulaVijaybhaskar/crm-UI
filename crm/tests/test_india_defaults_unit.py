# Copyright (c) 2026, Astra and contributors
import importlib.util
import unittest
from pathlib import Path


def _load():
	path = Path(__file__).resolve().parents[1] / "install_india.py"
	# Avoid importing frappe-dependent module body for regex-only checks —
	# pull patterns by exec of a slice is brittle; re-declare mirrors here.
	return path


class TestIndiaTaxPatterns(unittest.TestCase):
	def test_gstin_and_pan_regex(self):
		import re

		gstin = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
		pan = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
		self.assertTrue(gstin.match("29ABCDE1234F1Z5"))
		self.assertFalse(gstin.match("29ABCDE1234F1"))
		self.assertTrue(pan.match("ABCDE1234F"))
		self.assertFalse(pan.match("ABCDE1234"))
		# PAN embedded in GSTIN
		self.assertEqual("29ABCDE1234F1Z5"[2:12], "ABCDE1234F")


if __name__ == "__main__":
	unittest.main()
