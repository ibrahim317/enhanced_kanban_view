import re

import frappe


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

	reference_doctype = frappe.db.get_value("Kanban Board", kanban_board_name, "reference_doctype")

	rows = frappe.db.sql(
		"""
		SELECT DISTINCT child.field_name
		FROM `tabKanban Board Rule` AS rule
		JOIN `tabKanban Rule Field` AS child ON child.parent = rule.name
		LEFT JOIN `tabKanban Board Column` AS col ON col.name = rule.kanban_board_column
		WHERE rule.kanban_board = %(board)s
			AND (col.column_name = %(column)s OR rule.kanban_board_column = %(column)s)
		""",
		values={"board": kanban_board_name, "column": column_name},
		as_dict=True,
	)

	fields = []
	for row in rows:
		field_name = _resolve_legacy_field_name(row.field_name, reference_doctype)
		if field_name and field_name not in fields:
			fields.append(field_name)
	return fields
