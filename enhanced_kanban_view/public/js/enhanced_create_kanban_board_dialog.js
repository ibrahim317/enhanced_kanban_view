frappe.views.KanbanView.show_kanban_dialog = function (doctype) {
	let dialog = new_kanban_dialog();
	dialog.show();

	function make_kanban_board(board_name, field_name, project) {
		return frappe.call({
			method: "enhanced_kanban_view.api.kanban_board.quick_kanban_board",
			args: {
				doctype,
				board_name,
				field_name,
				project,
			},
			callback: function (r) {
				var kb = r.message;
				if (kb.filters) {
					frappe.provide("frappe.kanban_filters");
					frappe.kanban_filters[kb.kanban_board_name] = kb.filters;
				}
				frappe.set_route("List", doctype, "Kanban", kb.kanban_board_name);
			},
		});
	}

	function new_kanban_dialog() {
		/* Kanban dialog can show either "Save" or "Customize Form" option depending if any Select fields exist in the DocType for Kanban creation
		 */

		const fields = frappe.get_meta(doctype).fields.filter((df) => {
			return (df.fieldtype === "Select" || df.fieldtype === "Link") && df.fieldname !== "kanban_column";
		});
		const dialog_fields = get_fields_for_dialog(fields);
		const to_save = fields.length > 0;
		const primary_action_label = to_save ? __("Save") : __("Customize Form");
		const dialog_title = to_save ? __("New Kanban Board") : __("No Select Field Found");

		let primary_action = () => {
			if (to_save) {
				const values = dialog.get_values();
				make_kanban_board(values.board_name, values.field_name, values.project).then(
					() => dialog.hide(),
					(err) => frappe.msgprint(err)
				);
			} else {
				frappe.set_route("Form", "Customize Form", { doc_type: doctype });
			}
		};

		return new frappe.ui.Dialog({
			title: dialog_title,
			fields: dialog_fields,
			primary_action_label,
			primary_action,
		});
	}

	function get_fields_for_dialog(fields) {
		if (!fields.length) {
			return [
				{
					fieldtype: "HTML",
					options: `
					<div>
						<p class="text-medium">
						${__(
							'No fields found that can be used as a Kanban Column. Use the Customize Form to add a Custom Field of type "Select" or "Link".'
						)}
						</p>
					</div>
				`,
				},
			];
		}

		let dialog_fields = [
			{
				fieldtype: "Data",
				fieldname: "board_name",
				label: __("Kanban Board Name"),
				reqd: 1,
				description: ["Note", "ToDo"].includes(doctype)
					? __("This Kanban Board will be private")
					: "",
			},
			{
				fieldtype: "Select",
				fieldname: "field_name",
				label: __("Columns based on"),
				options: fields.map((df) => ({ label: df.label, value: df.fieldname })),
				default: fields[0].fieldname,
				reqd: 1,
			},
		];

		if (doctype === "Task") {
			dialog_fields.push({
				fieldtype: "Link",
				fieldname: "project",
				label: __("Project"),
				options: "Project",
			});
		}

		return dialog_fields;
	}
};

