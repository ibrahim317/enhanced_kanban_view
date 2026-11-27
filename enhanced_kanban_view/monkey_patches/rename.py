from types import SimpleNamespace

import frappe
import frappe.model.rename_doc
from frappe.utils.data import sbool
from frappe.utils.scheduler import is_scheduler_inactive

orig_rename = frappe.model.rename_doc.update_document_title


@frappe.whitelist(methods=["POST"])
def custom_rename(
	*,
	doctype: str,
	docname: str,
	title: str | None = None,
	name: str | None = None,
	merge: bool = False,
	enqueue: bool = False,
	**kwargs,
):
	old_name = docname
	# The core endpoint also accepts the legacy `new_name` kwarg.
	new_name = kwargs.get("new_name") or name
	rename_queued = sbool(enqueue) and not is_scheduler_inactive()

	result = orig_rename(
		doctype=doctype,
		docname=docname,
		title=title,
		name=name,
		merge=merge,
		enqueue=enqueue,
		**kwargs,
	)

	# A queued rename happens in a background job, so there is nothing to sync
	# yet in this request.
	if new_name and old_name != new_name and not rename_queued:
		# The sync helper only needs the DocType, not a real Document.
		doc_mock = SimpleNamespace(doctype=doctype)
		frappe.get_attr(
			"enhanced_kanban_view.enhanced_kanban_view.utils.update_kanban_columns_after_rename"
		)(doc_mock, old_name, new_name)

	return result


frappe.model.rename_doc.update_document_title = custom_rename
