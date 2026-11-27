"""Server-side enforcement of the per-column rules configured on Kanban boards.

The v2 Kanban engine moves cards with ``frappe.client.set_value`` /
``frappe.client.bulk_update``, so rules cannot be enforced only by the client.
This module is wired to the wildcard ``validate`` doc_event in hooks.py.

The wildcard hook runs for every saved document, so rule definitions are built
once and cached. Saving any of the configuration DocTypes clears the cache.
"""

from collections import defaultdict

import frappe
from frappe import _

from enhanced_kanban_view.api.kanban_board_rule import _resolve_legacy_field_name

CACHE_KEY = "enhanced_kanban:column_rules"

# These DocTypes define the rules (or are their child rows). Validating them
# would only add work and could recursively re-enter this hook.
CONFIG_DOCTYPES = {
	"Kanban Board",
	"Kanban Board Rule",
	"Kanban Rule Field",
	"Kanban Board Column",
}

SKIP_FLAGS = (
	"in_import",
	"in_install",
	"in_migrate",
	"in_patch",
	"ignore_kanban_rules",
)


def _is_empty(value) -> bool:
	if value is None:
		return True
	if isinstance(value, str) and not value.strip():
		return True
	if isinstance(value, (list, tuple, dict)) and not value:
		return True
	return False


def _cache():
	"""Work with both ``frappe.cache()`` (<= v16) and ``frappe.cache`` (v17)."""
	cache = getattr(frappe, "cache")
	return cache if hasattr(cache, "get_value") else cache()


def clear_rules_cache(doc=None, method=None):
	"""Drop the cached rule map after a board, rule or field is changed."""
	_cache().delete_value(CACHE_KEY)


def _build_rules():
	"""Build ``{doctype: {board: {field_name, columns}}}`` from the database."""
	boards = frappe.get_all(
		"Kanban Board", fields=["name", "reference_doctype", "field_name"]
	)
	board_map = {
		b.name: b for b in boards if b.field_name and b.reference_doctype
	}
	if not board_map:
		return {}

	rules = frappe.get_all(
		"Kanban Board Rule",
		filters={"kanban_board": ["in", list(board_map)]},
		fields=["name", "kanban_board", "kanban_board_column"],
	)
	if not rules:
		return {}

	column_names = [r.kanban_board_column for r in rules if r.kanban_board_column]
	column_rows = (
		frappe.get_all(
			"Kanban Board Column",
			filters={"name": ["in", column_names]},
			fields=["name", "column_name"],
		)
		if column_names
		else []
	)
	column_titles = {row.name: row.column_name for row in column_rows}

	field_rows = frappe.get_all(
		"Kanban Rule Field",
		filters={"parent": ["in", [r.name for r in rules]]},
		fields=["parent", "field_name"],
	)
	fields_by_rule = defaultdict(list)
	for row in field_rows:
		if row.field_name:
			fields_by_rule[str(row.parent)].append(row.field_name)

	by_doctype = {}
	for rule in rules:
		board = board_map.get(rule.kanban_board)
		if not board:
			continue

		# Rules point at a Kanban Board Column child row. Legacy rows may store
		# the column title instead, so accept both spellings.
		column = column_titles.get(rule.kanban_board_column) or rule.kanban_board_column
		# Rule names can come back as ints while child parents are strings.
		required = fields_by_rule.get(str(rule.name))
		if not column or not required:
			continue

		entry = (
			by_doctype.setdefault(board.reference_doctype, {})
			.setdefault(board.name, {"field_name": board.field_name, "columns": {}})
		)
		bucket = entry["columns"].setdefault(column, [])
		for key in (rule.kanban_board_column, column):
			if key:
				entry["columns"][key] = bucket
		for field_name in required:
			if field_name not in bucket:
				bucket.append(field_name)

	return by_doctype


def validate_kanban_rules(doc, method=None):
	"""Throw when a card is in a column whose rules have unfilled required fields."""
	if doc.doctype in CONFIG_DOCTYPES or any(
		getattr(frappe.flags, flag, False) for flag in SKIP_FLAGS
	):
		return

	meta = frappe.get_meta(doc.doctype)
	if meta.istable or meta.issingle:
		return

	rules = _cache().get_value(CACHE_KEY, generator=_build_rules) or {}
	board_rules = rules.get(doc.doctype)
	if not board_rules:
		return

	missing_by_board = {}
	for board_name, config in board_rules.items():
		column = doc.get(config["field_name"])
		required = config["columns"].get(column)
		if not required:
			continue

		missing = []
		for field_name in required:
			field_name = _resolve_legacy_field_name(field_name, doc.doctype)
			if field_name and _is_empty(doc.get(field_name)):
				df = meta.get_field(field_name)
				missing.append(df.label if df else field_name)

		if missing:
			missing_by_board.setdefault(board_name, set()).update(missing)

	if missing_by_board:
		details = "; ".join(
			"{0}: {1}".format(board, ", ".join(sorted(fields)))
			for board, fields in sorted(missing_by_board.items())
		)
		frappe.throw(
			_("The following fields are required for this Kanban column: {0}").format(details)
		)
