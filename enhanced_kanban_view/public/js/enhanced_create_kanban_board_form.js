frappe.ui.form.on("Kanban Board", {
	onload: function (frm) {
		const handlers = frappe.ui.form.handlers["Kanban Board"];

		if (!handlers) {
			return;
		}

		handlers.reference_doctype = [
			function (frm) {
				if (!frm.doc.reference_doctype) return;

				frappe.model.with_doctype(frm.doc.reference_doctype, function () {
					var options = $.map(frappe.get_meta(frm.doc.reference_doctype).fields, function (d) {
						if (
							d.fieldname &&
							(d.fieldtype === "Select" || d.fieldtype === "Link") &&
							frappe.model.no_value_type.indexOf(d.fieldtype) === -1
						) {
							return d.fieldname;
						}
						return null;
					});
					frm.set_df_property("field_name", "options", options.join("\n"));
					frm.get_field("field_name").refresh();
				});
			},
		];

		handlers.field_name = [
			function (frm) {
				var field = frappe.meta.get_field(frm.doc.reference_doctype, frm.doc.field_name);
				frm.doc.columns = [];
				if (!field) {
					frm.refresh_field("columns");
					return;
				}
				if (field.fieldtype === "Link") {
					frappe.db
						.get_list(field.options, {
							fields: ["name"],
							limit_page_length: 15,
						})
						.then(function (records) {
							if (records && records.length) {
								records.forEach(function (record) {
									frm.add_child("columns", {
										column_name: record.name,
									});
								});
								frm.refresh_field("columns");
							}
						})
						.catch(function () {
							// Handle error if the linked DocType is not found or accessible
							frappe.msgprint({
								title: __("Error"),
								indicator: "red",
								message: __(
									"Could not fetch columns for field '{0}'. The linked DocType '{1}' may not exist or you may not have permission to view it.",
									[frm.doc.field_name, field.options]
								),
							});
						});
				} else if (field.fieldtype === "Select") {
					field.options &&
						field.options.split("\n").forEach(function (o) {
							o = o.trim();
							if (!o) return;
							var d = frm.add_child("columns");
							d.column_name = o;
						});
					frm.refresh();
				}
			},
		];

		// Because the core 'onload' handler has already fired and triggered the
		// original 'reference_doctype' logic, we need to trigger it again to
		// execute our new, overriding function.
		frm.trigger("reference_doctype");
	},
});
