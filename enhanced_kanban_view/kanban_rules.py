"""Server-side enforcement of the per-column rules configured on Kanban boards.

The v2 Kanban engine moves cards with ``frappe.client.set_value`` /
``frappe.client.bulk_update``, so rules cannot be enforced only by the client.
This module is wired to the wildcard ``validate`` doc_event in hooks.py.
"""

import frappe
from frappe import _

from enhanced_kanban_view.api.kanban_board_rule import _resolve_legacy_field_name


def _is_empty(value) -> bool:
	if value is None:
		return True
	if isinstance(value, str) and not value.strip():
		return True
	if isinstance(value, (list, tuple, dict)) and not value:
		return True
	return False


def validate_kanban_rules(doc, method=None):
	"""Throw when a card is in a column whose rules have unfilled required fields."""
	if getattr(frappe.flags, "in_import", False) or getattr(
		frappe.flags, "ignore_kanban_rules", False
	):
		return

	boards = frappe.get_all(
		"Kanban Board",
		filters={"reference_doctype": doc.doctype},
		fields=["name", "field_name"],
	)
	board_fields = {b.name: b.field_name for b in boards if b.field_name}
	if not board_fields:
		return

	rules = frappe.get_all(
		"Kanban Board Rule",
		filters={"kanban_board": ["in", list(board_fields)]},
		fields=["name", "kanban_board", "kanban_board_column"],
	)
	if not rules:
		return

	# Rules point at the Kanban Board Column child row. Legacy rows may have the
	# column title stored directly instead of a child row name.
	column_rows = frappe.get_all(
		"Kanban Board Column",
		filters={
			"name": [
				"in",
				[r.kanban_board_column for r in rules if r.kanban_board_column],
			]
		},
		fields=["name", "column_name"],
	)
	column_titles = {row.name: row.column_name for row in column_rows}

	meta = frappe.get_meta(doc.doctype)
	missing_by_rule = {}
	for rule in rules:
		column = column_titles.get(rule.kanban_board_column) or rule.kanban_board_column
		board_field = board_fields.get(rule.kanban_board)
		if not column or not board_field or doc.get(board_field) != column:
			continue

		required = frappe.get_all(
			"Kanban Rule Field", filters={"parent": rule.name}, pluck="field_name"
		)
		missing = []
		for field_name in required:
			field_name = _resolve_legacy_field_name(field_name, doc.doctype)
			if field_name and _is_empty(doc.get(field_name)):
				df = meta.get_field(field_name)
				missing.append(df.label if df else field_name)

		if missing:
			missing_by_rule.setdefault(rule.kanban_board, set()).update(missing)

	if missing_by_rule:
		details = "; ".join(
			"{0}: {1}".format(board, ", ".join(sorted(fields)))
			for board, fields in sorted(missing_by_rule.items())
		)
		frappe.throw(
			_("The following fields are required for this Kanban column: {0}").format(details)
		)
