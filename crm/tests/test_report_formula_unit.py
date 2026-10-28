# Copyright (c) 2026, Astra and contributors
# Pure unit tests for the reports formula parser (no Frappe site required).

import importlib.util
import unittest
from pathlib import Path


def _load():
	path = Path(__file__).resolve().parents[1] / "api" / "reports" / "formula.py"
	spec = importlib.util.spec_from_file_location("crm_report_formula", path)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


class TestReportFormula(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.f = _load()

	def test_basic_arithmetic(self):
		self.assertEqual(self.f.evaluate_formula("1 + 2 * 3", {}), 7.0)
		self.assertEqual(self.f.evaluate_formula("(1 + 2) * 3", {}), 9.0)
		self.assertEqual(self.f.evaluate_formula("{won} / {deals}", {"won": 100, "deals": 4}), 25.0)

	def test_unicode_operators(self):
		self.assertEqual(
			self.f.evaluate_formula("{won} ÷ {deals} × 100", {"won": 2, "deals": 4}),
			50.0,
		)

	def test_win_rate_style(self):
		result = self.f.evaluate_formula(
			"{won} / {total} * 100",
			{"won": 14, "total": 49},
		)
		self.assertAlmostEqual(result, 28.5714, places=3)

	def test_rejects_empty(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.validate_formula("   ")

	def test_rejects_unknown_ref(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("{won} / {missing}", {"won": 1})

	def test_rejects_injection_attribute(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("__import__('os').system('id')", {})

	def test_rejects_injection_call(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("eval('1+1')", {})

	def test_rejects_injection_name_lookup(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("os.system", {})

	def test_rejects_brackets_and_strings(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("{'a': 1}", {})
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula('"hi"', {})

	def test_rejects_power_and_modulo(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("2 ** 3", {})
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("5 % 2", {})

	def test_division_by_zero(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.evaluate_formula("{a} / {b}", {"a": 1, "b": 0})

	def test_unary_minus(self):
		self.assertEqual(self.f.evaluate_formula("-{a} + 5", {"a": 2}), 3.0)

	def test_whitelist_refs(self):
		with self.assertRaises(self.f.FormulaError):
			self.f.validate_formula("{won} + {secret}", allowed_refs={"won"})
