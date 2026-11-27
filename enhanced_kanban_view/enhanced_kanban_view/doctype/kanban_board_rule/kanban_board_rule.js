frappe.ui.form.on("Kanban Board Rule", {
	refresh: function (frm) {
		if (frm.doc.kanban_board) {
			frm.trigger("kanban_board");
		}
	},

	kanban_board: function (frm) {
		if (!frm.doc.kanban_board) return;

		frm.call({
			doc: frm.doc,
			method: "get_kanban_board_data",
			args: { board_name: frm.doc.kanban_board },
			callback: function (r) {
				const data = r.message || {};

				frm.set_query("kanban_board_column", function () {
					return {
						filters: [["column_name", "in", data.columns || []]],
					};
				});
				frm.refresh_field("kanban_board_column");

				// Options carry the real fieldname as the stored value and the
				// human readable label for display, e.g. "Status (status)".
				const options = (data.fields || []).map((f) => ({
					label: f.label,
					value: f.value,
				}));

				const child_grid = frm.get_field("required_fields").grid;
				child_grid.update_docfield_property("field_name", "options", options);
				frm.refresh_field("required_fields");
			},
		});
	},
});
