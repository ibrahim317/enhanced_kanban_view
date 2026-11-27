import frappe

def check_for_connected_kanban_boards(target_doctype):
	sql = """
		SELECT
			candidates.doctype,
			candidates.fieldname,
			candidates.reason,
			kb.name AS kanban_board_name
		FROM (
			-- Subquery Part 1: Find direct links in tabDocField
			SELECT
				parent AS doctype,
				fieldname,
				'Direct Link' as reason
			FROM
				`tabDocField`
			WHERE
				fieldtype = 'Link' AND options = %(doctype)s

			UNION

			-- Subquery Part 2: Find links created by a Property Setter
			SELECT
				ps.doc_type AS doctype,
				ps.field_name AS fieldname,
				'Property Setter' as reason
			FROM
				`tabProperty Setter` ps
			WHERE
				ps.property = 'options'
				AND ps.value = %(doctype)s

		) AS candidates
		-- Join the combined candidates with Kanban Boards
		JOIN `tabKanban Board` AS kb
			ON candidates.doctype = kb.reference_doctype
			AND candidates.fieldname = kb.field_name
	"""
	return frappe.db.sql(sql, {"doctype": target_doctype}, as_dict=True)

def update_kanban_columns_after_insert(self):
	# check if self.doctype has connected kanban_boards
	# if it has update that kanban to take the kanban_columns from self.doctype's records names (name of the records)
	kanban_boards = check_for_connected_kanban_boards(self.doctype)
	for kanban_board in kanban_boards:
		kb_doc = frappe.get_doc("Kanban Board", kanban_board.kanban_board_name)
		if not any(col.column_name == self.name for col in kb_doc.get("columns")):
			kb_doc.append("columns", {"column_name": self.name})
			kb_doc.save(ignore_permissions=True)

def update_kanban_columns_after_rename(self, old_name, new_name):
	if old_name == new_name:
		return

	kanban_boards = check_for_connected_kanban_boards(self.doctype)
	for kanban_board in kanban_boards:
		kb_doc = frappe.get_doc("Kanban Board", kanban_board.kanban_board_name)
		column_to_update = next((col for col in kb_doc.get("columns") if col.column_name == old_name), None)

		if column_to_update:
			column_to_update.column_name = new_name
			kb_doc.save(ignore_permissions=True)

def update_kanban_columns_after_delete(target_doctype, items):
	if isinstance(items, str):
		items = frappe.parse_json(items) or []

	kanban_boards = check_for_connected_kanban_boards(target_doctype)
	for kanban_board in kanban_boards:
		kb_doc = frappe.get_doc("Kanban Board", kanban_board.kanban_board_name)
		columns = kb_doc.get("columns")

		# Create a list of columns to remove
		columns_to_remove = [col for col in columns if col.column_name in items]

		# Remove all matching columns
		for col in columns_to_remove:
			columns.remove(col)

		# Save only once after removing all columns
		if columns_to_remove:
			kb_doc.save(ignore_permissions=True)
