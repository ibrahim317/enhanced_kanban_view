import re

import frappe
from frappe import _


MAX_RULE_FIELDS = 100


def _resolve_legacy_field_name(field_name: str, reference_doctype: str) -> str:
	"""Normalize values saved by older versions of the rule child table.

	Older releases stored labels such as ``Status (status)`` or
	``Priority (Custom)``. New records store the bare fieldname because the
	client sets ``{label, value}`` options on the Select field.
	"""
	value = (field_name or "").strip()
	match = re.search(r"\(([^)]+)\)$", value)
	if not match:
		return value

	suffix = match.group(1).strip()
	if suffix.lower() != "custom":
		return suffix

	# "Label (Custom)" does not contain the fieldname: resolve it by label.
	label = value[: value.rfind("(")].strip()
	return (
		frappe.db.get_value(
			"Custom Field", {"dt": reference_doctype, "label": label}, "fieldname"
		)
		or value
	)


@frappe.whitelist()
def get_additional_fields(kanban_board_name, column_name):
	"""Return the fieldnames required by rules configured for a board column.

	The rule stores a Link to a ``Kanban Board Column`` child row, whose ``name``
	is a hash. Older data may also have stored the column title directly, so both
	forms are accepted here.
	"""
	frappe.has_permission("Kanban Board", "read", doc=kanban_board_name, throw=True)

	board = frappe.db.get_value(
		"Kanban Board", kanban_board_name, ["reference_doctype", "field_name"], as_dict=True
	)
	if not board or not board.reference_doctype:
		frappe.throw(_("Kanban Board {0} does not exist").format(kanban_board_name))
	frappe.has_permission(board.reference_doctype, "read", throw=True)

	if not isinstance(column_name, str) or not column_name.strip():
		return []

	rows = frappe.db.sql(
		"""
		SELECT DISTINCT child.field_name
		FROM `tabKanban Board Rule` AS rule
		JOIN `tabKanban Rule Field` AS child ON child.parent = rule.name
		LEFT JOIN `tabKanban Board Column` AS col ON col.name = rule.kanban_board_column
		WHERE rule.kanban_board = %(board)s
			AND (col.column_name = %(column)s OR rule.kanban_board_column = %(column)s)
		LIMIT %(limit)s
		""",
		values={
			"board": kanban_board_name,
			"column": column_name,
			"limit": MAX_RULE_FIELDS,
		},
		as_dict=True,
	)

	# Legacy rules can reference fields that no longer exist; sending those to
	# quick entry would break the dialog.
	meta = frappe.get_meta(board.reference_doctype)
	fields = []
	for row in rows:
		field_name = _resolve_legacy_field_name(row.field_name, board.reference_doctype)
		if field_name and field_name not in fields and meta.has_field(field_name):
			fields.append(field_name)
	return fields
