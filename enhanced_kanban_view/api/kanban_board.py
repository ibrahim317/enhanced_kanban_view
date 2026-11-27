import frappe
from frappe import _


@frappe.whitelist()
def quick_kanban_board(doctype, board_name, field_name, project=None):
	"""Create a KanbanBoard with columns derived from a Select or Link field."""
	frappe.has_permission(doctype, "read", throw=True)

	meta = frappe.get_meta(doctype)
	field = meta.get_field(field_name)
	if not field or field.fieldtype not in ("Select", "Link"):
		frappe.throw(
			_("Field {0} must be a Select or Link field on {1}").format(field_name, doctype)
		)

	doc = frappe.new_doc("Kanban Board")
	doc.kanban_board_name = board_name
	doc.reference_doctype = doctype
	doc.field_name = field_name

	if project:
		frappe.has_permission("Project", "read", doc=project, throw=True)
		doc.filters = frappe.as_json([[doctype, "project", "=", project]])

	if field.fieldtype == "Select":
		options = (field.options or "").split("\n")
	else:
		options = frappe.get_all(
			field.options,
			filters={},
			pluck="name",
			limit_page_length=15,
		)

	for column in options:
		column = (column or "").strip()
		if column:
			doc.append("columns", {"column_name": column})

	if doctype in ["Note", "ToDo"]:
		doc.private = 1

	doc.save()
	return doc
