import frappe.desk.reportview

orig_delete = frappe.desk.reportview.delete_items

@frappe.whitelist(methods=["POST", "DELETE"])
def custom_delete():
    doctype = frappe.form_dict.get("doctype")
    items = frappe.parse_json(frappe.form_dict.get("items")) or []
    result = orig_delete()
    frappe.get_attr("enhanced_kanban_view.enhanced_kanban_view.utils.update_kanban_columns_after_delete")(doctype, items)
    return result

frappe.desk.reportview.delete_items = custom_delete
