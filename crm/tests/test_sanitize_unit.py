# Copyright (c) 2026, Astra and contributors
# Lightweight checks that do not require a Frappe site (importlib load).

import importlib.util
import unittest
from pathlib import Path


def _load():
	path = Path(__file__).resolve().parents[1] / "utils" / "sanitize.py"
	spec = importlib.util.spec_from_file_location("crm_sanitize", path)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


class TestSanitize(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.s = _load()

	def test_strips_script_and_handlers(self):
		out = self.s.sanitize_html(
			'<p>Hi<script>alert(1)</script></p><a href="javascript:alert(1)" onclick="x">x</a>'
		)
		self.assertNotIn("<script", out.lower())
		self.assertNotIn("javascript:", out.lower())
		self.assertNotIn("onclick", out.lower())

	def test_keeps_formatting_and_mentions(self):
		out = self.s.sanitize_html(
			'<p><strong>Bold</strong> <span data-type="mention" data-id="a@b.com">A</span></p>'
		)
		self.assertIn("<strong>Bold</strong>", out)
		self.assertIn('data-type="mention"', out)

	def test_plain_text_strips_tags(self):
		self.assertEqual(self.s.sanitize_text("<b>Ada</b> & co"), "Ada & co")
		self.assertEqual(self.s.sanitize_text("+919876543210"), "+919876543210")


if __name__ == "__main__":
	unittest.main()
