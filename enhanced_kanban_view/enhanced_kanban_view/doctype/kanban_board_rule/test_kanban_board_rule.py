# Copyright (c) 2025, Ibrahim Aboelsoud and Contributors
# See license.txt

import frappe
from frappe import ValidationError
from frappe.tests import IntegrationTestCase

from enhanced_kanban_view.api.kanban_board_rule import get_additional_fields


class IntegrationTestKanbanBoardRule(IntegrationTestCase):
	"""Integration tests for KanbanBoardRule.

	Use these module variables to add/remove to/from that list
	"""
	doctype = "Kanban Board Rule"

	def setUp(self):
		# IntegrationTestCase rolls back successful tests, but failed runs can
		# leave boards behind. Start from a clean slate.
		for name in frappe.get_all(
			"Kanban Board Rule",
			filters={"kanban_board": ["like", "Test Enhanced Kanban Board %"]},
			pluck="name",
		):
			frappe.delete_doc("Kanban Board Rule", name, force=True, ignore_permissions=True)
		for name in frappe.get_all(
			"Kanban Board", filters={"name": ["like", "Test Enhanced Kanban Board %"]}, pluck="name"
		):
			frappe.delete_doc("Kanban Board", name, force=True, ignore_permissions=True)
		for name in frappe.get_all(
			"Custom Field",
			filters={"fieldname": ["like", "test_enhanced_kanban_%"]},
			pluck="name",
		):
			frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)

		self.board_name = f"Test Enhanced Kanban Board {frappe.generate_hash(length=6)}"
		self.board = frappe.get_doc(
			{
				"doctype": "Kanban Board",
				"kanban_board_name": self.board_name,
				"reference_doctype": "ToDo",
				"field_name": "status",
				"columns": [
					{"column_name": "Open"},
					{"column_name": "Open Archived"},
					{"column_name": "Closed"},
				],
			}
		).insert(ignore_permissions=True)
		self.open_column = next(c for c in self.board.columns if c.column_name == "Open")
		archived_column = next(c for c in self.board.columns if c.column_name == "Open Archived")
		self.rule = frappe.get_doc(
			{
				"doctype": "Kanban Board Rule",
				"kanban_board": self.board.name,
				"kanban_board_column": self.open_column.name,
				"required_fields": [
					{"field_doctype": "DocField", "field_name": "priority"},
				],
			}
		).insert(ignore_permissions=True)
		self.archived_rule = frappe.get_doc(
			{
				"doctype": "Kanban Board Rule",
				"kanban_board": self.board.name,
				"kanban_board_column": archived_column.name,
				"required_fields": [
					{"field_doctype": "DocField", "field_name": "description"},
				],
			}
		).insert(ignore_permissions=True)

	def test_get_additional_fields_matches_exact_column(self):
		# A LIKE-based lookup would also match "Open Archived" here.
		self.assertEqual(get_additional_fields(self.board.name, "Open"), ["priority"])
		self.assertEqual(get_additional_fields(self.board.name, "Closed"), [])

	def test_legacy_custom_label_is_resolved(self):
		fieldname = f"test_enhanced_kanban_{frappe.generate_hash(length=5)}"
		label = f"Enhanced Kanban Test Field {fieldname}"
		custom = frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "ToDo",
				"fieldname": fieldname,
				"label": label,
				"fieldtype": "Data",
			}
		).insert(ignore_permissions=True)
		self.rule.required_fields[0].field_name = f"{label} (Custom)"
		self.rule.save(ignore_permissions=True)

		self.assertEqual(get_additional_fields(self.board.name, "Open"), [fieldname])
		frappe.delete_doc("Custom Field", custom.name, force=True, ignore_permissions=True)

	def test_server_side_validation_blocks_missing_required_field(self):
		with self.assertRaises(ValidationError):
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"description": "Enhanced Kanban test",
					"status": "Open",
					"priority": "",  # override the ToDo default
				}
			).insert(ignore_permissions=True)

	def test_rule_changes_are_visible_after_the_cache_is_warm(self):
		# The first validation warms the cached rule map.
		with self.assertRaises(ValidationError):
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"description": "Enhanced Kanban test",
					"status": "Open",
					"priority": "",
				}
			).insert(ignore_permissions=True)

		frappe.delete_doc(
			"Kanban Board Rule", self.rule.name, force=True, ignore_permissions=True
		)
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "Enhanced Kanban test",
				"status": "Open",
				"priority": "",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(todo.status, "Open")

	def test_server_side_validation_passes_when_field_is_filled(self):
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": "Enhanced Kanban test",
				"status": "Open",
				"priority": "High",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(todo.priority, "High")

	def test_other_columns_are_not_validated(self):
		todo = frappe.get_doc(
			{"doctype": "ToDo", "description": "Enhanced Kanban test", "status": "Closed"}
		).insert(ignore_permissions=True)
		self.assertEqual(todo.status, "Closed")
