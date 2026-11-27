# Copyright (c) 2025, Ibrahim Aboelsoud and contributors
# For license information, please see license.txt

import typing
import frappe
from frappe.model.document import Document

from typing import TypedDict

class KanbanBoard(Document):
    reference_doctype: str

class KanbanBoardData(TypedDict):
    columns: list[str]
    fields: list[dict]

class KanbanBoardColumn:
    def __init__(self, column_name: str):
        self.column_name = column_name


class KanbanBoardRule(Document):
    @frappe.whitelist()
    def get_kanban_board_data(self, board_name: str) -> KanbanBoardData:
        """
        Given a Kanban Board name, returns its columns and a complete, formatted
        list of fields from its reference DocType. This is designed for direct
        use by a frappe.call from the client.
        """
        if not board_name:
            return KanbanBoardData(columns=[], fields=[])

        frappe.has_permission("Kanban Board", "read", doc=board_name, throw=True)

        try:
            kanban_board_doc = typing.cast(KanbanBoard, frappe.get_doc("Kanban Board", board_name))
            reference_doctype = kanban_board_doc.reference_doctype
        except frappe.DoesNotExistError:
            return KanbanBoardData(columns=[], fields=[]) # Return empty if board not found

        # Get column names
        columns = typing.cast(list[KanbanBoardColumn], kanban_board_doc.get("columns", []))
        columns = [col.column_name for col in columns]

        # Get standard fields from metadata
        meta = frappe.get_meta(reference_doctype)
        standard_fields = [
            {"value": f.fieldname, "label": f"{f.label} ({f.fieldname})"}
            for f in meta.fields if f.fieldname
        ]

        # Get Custom Fields
        custom_fields_docs = frappe.get_all(
            "Custom Field",
            filters={"dt": reference_doctype},
            fields=["fieldname", "label"]
        )
        custom_fields = [
            {"value": f.fieldname, "label": f"{f.label or f.fieldname} ({f.fieldname})"}
            for f in custom_fields_docs
        ]

        all_fields = sorted(standard_fields + custom_fields, key=lambda x: x["label"])

        return {
            "columns": columns,
            "fields": all_fields
        }