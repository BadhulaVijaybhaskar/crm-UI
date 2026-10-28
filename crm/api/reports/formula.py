# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Safe KPI formula evaluator.

Supports numbers, KPI references, + - * /, and parentheses only.
Never uses eval / safe_eval / exec.
"""

from __future__ import annotations

import ast
import math
import re
from typing import Mapping

__all__ = [
	"FormulaError",
	"evaluate_formula",
	"parse_formula",
	"validate_formula",
]

_REF = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_TOKEN = re.compile(
	r"""
	\s*(?:
		(?P<number>\d+(?:\.\d+)?) |
		(?P<ref>\{[A-Za-z_][A-Za-z0-9_]*\}) |
		(?P<op>[+\-*/()]) |
		(?P<bad>.)
	)
	""",
	re.VERBOSE,
)


class FormulaError(ValueError):
	"""Raised when a formula is invalid or unsafe."""


def validate_formula(formula: str, allowed_refs: set[str] | None = None) -> None:
	"""Validate syntax and optional reference whitelist. Raises FormulaError."""
	parse_formula(formula, allowed_refs=allowed_refs)


def parse_formula(formula: str, allowed_refs: set[str] | None = None) -> ast.Expression:
	"""Parse formula into a restricted AST Expression."""
	if formula is None or not str(formula).strip():
		raise FormulaError("Formula is empty")

	tokens = list(_tokenize(str(formula)))
	pos = 0

	def peek():
		return tokens[pos] if pos < len(tokens) else None

	def take():
		nonlocal pos
		tok = peek()
		if tok is None:
			raise FormulaError("Unexpected end of formula")
		pos += 1
		return tok

	def parse_expr():
		node = parse_term()
		while peek() and peek()[0] == "op" and peek()[1] in "+-":
			op = take()[1]
			right = parse_term()
			op_node = ast.Add() if op == "+" else ast.Sub()
			node = ast.BinOp(left=node, op=op_node, right=right)
		return node

	def parse_term():
		node = parse_factor()
		while peek() and peek()[0] == "op" and peek()[1] in "*/":
			op = take()[1]
			right = parse_factor()
			op_node = ast.Mult() if op == "*" else ast.Div()
			node = ast.BinOp(left=node, op=op_node, right=right)
		return node

	def parse_factor():
		tok = peek()
		if tok is None:
			raise FormulaError("Unexpected end of formula")
		if tok[0] == "op" and tok[1] == "+":
			take()
			return parse_factor()
		if tok[0] == "op" and tok[1] == "-":
			take()
			return ast.UnaryOp(op=ast.USub(), operand=parse_factor())
		if tok[0] == "op" and tok[1] == "(":
			take()
			node = parse_expr()
			closing = peek()
			if closing is None or closing != ("op", ")"):
				raise FormulaError("Missing closing parenthesis")
			take()
			return node
		if tok[0] == "number":
			take()
			return ast.Constant(value=float(tok[1]))
		if tok[0] == "ref":
			take()
			name = tok[1][1:-1]
			if allowed_refs is not None and name not in allowed_refs:
				raise FormulaError(f"Unknown KPI reference: {name}")
			return ast.Name(id=name, ctx=ast.Load())
		raise FormulaError(f"Unexpected token: {tok[1]!r}")

	tree = parse_expr()
	if peek() is not None:
		raise FormulaError(f"Unexpected trailing token: {peek()[1]!r}")
	return ast.Expression(body=tree)


def evaluate_formula(formula: str, values: Mapping[str, float | int | None]) -> float:
	"""Evaluate a formula with numeric KPI values.

	Division by zero raises FormulaError. Unknown refs raise FormulaError.
	"""
	refs_in_formula = set(_REF.findall(str(formula)))
	for ref in refs_in_formula:
		if ref not in values:
			raise FormulaError(f"Unknown KPI reference: {ref}")

	expr = parse_formula(formula, allowed_refs=set(values.keys()))
	env = {k: float(v or 0) for k, v in values.items()}
	return _eval_node(expr.body, env)


def _eval_node(node: ast.AST, env: dict[str, float]) -> float:
	if isinstance(node, ast.Constant):
		if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
			return float(node.value)
		raise FormulaError("Invalid constant")
	if isinstance(node, ast.Name):
		if node.id not in env:
			raise FormulaError(f"Unknown KPI reference: {node.id}")
		return float(env[node.id])
	if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
		return -_eval_node(node.operand, env)
	if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
		return _eval_node(node.operand, env)
	if isinstance(node, ast.BinOp):
		left = _eval_node(node.left, env)
		right = _eval_node(node.right, env)
		if isinstance(node.op, ast.Add):
			return left + right
		if isinstance(node.op, ast.Sub):
			return left - right
		if isinstance(node.op, ast.Mult):
			return left * right
		if isinstance(node.op, ast.Div):
			if right == 0:
				raise FormulaError("Division by zero")
			return left / right
		raise FormulaError("Operator not allowed")
	raise FormulaError(f"Expression not allowed: {type(node).__name__}")


def _tokenize(formula: str):
	formula = formula.replace("×", "*").replace("÷", "/").replace("−", "-")
	for m in _TOKEN.finditer(formula):
		if m.group("number"):
			yield ("number", m.group("number"))
		elif m.group("ref"):
			yield ("ref", m.group("ref"))
		elif m.group("op"):
			yield ("op", m.group("op"))
		else:
			bad = m.group("bad")
			if bad and not bad.isspace():
				raise FormulaError(f"Illegal character: {bad!r}")


def is_finite(value: float) -> bool:
	return isinstance(value, (int, float)) and math.isfinite(value)
