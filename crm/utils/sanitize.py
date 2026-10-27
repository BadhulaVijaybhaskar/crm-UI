# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""HTML / text sanitisation for notes, comments, summaries, and webhook strings."""

from __future__ import annotations

import re
from html import escape, unescape
from html.parser import HTMLParser

# Keep a conservative allowlist — rich notes/comments need basic formatting only.
_ALLOWED_TAGS = {
	"a",
	"b",
	"blockquote",
	"br",
	"code",
	"div",
	"em",
	"h1",
	"h2",
	"h3",
	"h4",
	"h5",
	"h6",
	"hr",
	"i",
	"li",
	"ol",
	"p",
	"pre",
	"span",
	"strong",
	"u",
	"ul",
}
_VOID = {"br", "hr"}
_ALLOWED_ATTRS = {
	"a": {"href", "title", "rel", "target"},
	"span": {"class", "data-type", "data-id", "data-label"},  # mention chips
	"div": {"class"},
	"p": {"class"},
	"code": {"class"},
	"pre": {"class"},
}
_SAFE_HREF = re.compile(r"^(https?:|mailto:|/|#)", re.I)
_SCRIPTISH = re.compile(r"^\s*javascript:", re.I)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_TAG_RE = re.compile(r"<[^>]+>")


class _SanitisingParser(HTMLParser):
	def __init__(self):
		super().__init__(convert_charrefs=True)
		self._out: list[str] = []
		self._skip_depth = 0

	def handle_starttag(self, tag, attrs):
		tag = tag.lower()
		if tag in {"script", "style", "iframe", "object", "embed", "link", "meta"}:
			self._skip_depth += 1
			return
		if self._skip_depth:
			return
		if tag not in _ALLOWED_TAGS:
			return
		allowed = _ALLOWED_ATTRS.get(tag, set())
		kept = []
		for attr, value in attrs:
			attr_l = (attr or "").lower()
			if attr_l.startswith("on") or attr_l not in allowed:
				continue
			val = value or ""
			if attr_l == "href" and (not _SAFE_HREF.match(val) or _SCRIPTISH.match(val)):
				continue
			kept.append(f'{attr_l}="{escape(val, quote=True)}"')
		attr_str = (" " + " ".join(kept)) if kept else ""
		if tag in _VOID:
			self._out.append(f"<{tag}{attr_str} />")
		else:
			self._out.append(f"<{tag}{attr_str}>")

	def handle_endtag(self, tag):
		tag = tag.lower()
		if tag in {"script", "style", "iframe", "object", "embed", "link", "meta"}:
			if self._skip_depth:
				self._skip_depth -= 1
			return
		if self._skip_depth or tag not in _ALLOWED_TAGS or tag in _VOID:
			return
		self._out.append(f"</{tag}>")

	def handle_data(self, data):
		if self._skip_depth:
			return
		self._out.append(escape(data))

	def handle_entityref(self, name):
		if self._skip_depth:
			return
		self._out.append(f"&{name};")

	def handle_charref(self, name):
		if self._skip_depth:
			return
		self._out.append(f"&#{name};")

	def result(self) -> str:
		return "".join(self._out)


def sanitize_html(html: str | None) -> str:
	"""Strip scripts/styles and disallowed tags/attrs from HTML content."""
	if not html:
		return ""
	parser = _SanitisingParser()
	try:
		parser.feed(str(html))
		parser.close()
	except Exception:
		return sanitize_text(html)
	return parser.result()


def sanitize_text(value: str | None, *, max_length: int | None = None) -> str:
	"""Plain-text sanitise: drop tags, collapse control chars, optional length cap."""
	if value is None:
		return ""
	text = _TAG_RE.sub(" ", str(value))
	text = unescape(text)
	text = _CONTROL.sub("", text)
	text = re.sub(r"[ \t]+\n", "\n", text)
	text = re.sub(r"[ \t]{2,}", " ", text).strip()
	if max_length is not None and len(text) > max_length:
		text = text[:max_length]
	return text


def escape_text(value: str | None) -> str:
	return escape(sanitize_text(value))
