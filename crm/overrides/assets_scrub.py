"""Strip browser-downloadable ``*.map`` sourcemaps from served asset trees.

Framework / base-image builds often leave ``.map`` files under ``sites/assets``.
Vite production already sets ``sourcemap: false``; this scrub is defence in depth
for anything that still lands on disk after ``bench build`` or image bake.
"""

from __future__ import annotations

import os
from pathlib import Path


def _candidate_roots() -> list[Path]:
	roots: list[Path] = []
	try:
		import frappe

		# sites/assets (served) and the app's public frontend bundle
		bench = Path(frappe.utils.get_bench_path())
		roots.append(bench / "sites" / "assets")
		app_path = Path(frappe.get_app_path("crm")).parent  # .../apps/crm
		roots.append(app_path / "crm" / "public" / "frontend")
		roots.append(app_path / "crm" / "public" / "js")
	except Exception:
		# Offline / unit contexts — scrub relative to repo if present
		here = Path(__file__).resolve()
		repo = here.parents[2]  # crm/overrides -> repo root when installed as apps/crm
		roots.append(repo / "crm" / "public" / "frontend")
		# When running from the app checkout itself
		roots.append(here.parents[1] / "public" / "frontend")
	return roots


def strip_sourcemaps(extra_roots: list[str | os.PathLike] | None = None) -> int:
	"""Delete ``*.map`` under known asset roots. Returns count removed."""
	removed = 0
	roots = list(_candidate_roots())
	if extra_roots:
		roots.extend(Path(p) for p in extra_roots)

	seen: set[Path] = set()
	for root in roots:
		try:
			root = root.resolve()
		except Exception:
			continue
		if root in seen or not root.is_dir():
			continue
		seen.add(root)
		for dirpath, _dirnames, filenames in os.walk(root):
			for name in filenames:
				if not name.endswith(".map"):
					continue
				path = Path(dirpath) / name
				try:
					path.unlink()
					removed += 1
				except OSError:
					pass
	return removed


def after_migrate_strip_sourcemaps() -> None:
	"""after_migrate hook entry — best-effort, never fail migrate."""
	try:
		strip_sourcemaps()
	except Exception:
		try:
			import frappe

			frappe.log_error(title="Astra assets scrub: strip_sourcemaps failed")
		except Exception:
			pass
