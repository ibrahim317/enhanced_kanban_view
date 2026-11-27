// Kanban v2 integration for Enhanced Kanban View.
//
// v2 exposes a per-DocType settings registry and engine callbacks. We use those
// instead of replacing frappe.views.KanbanBoard: no core code is copied, so the
// board keeps realtime updates, virtualisation and multi-card drags.

const ENHANCED_RULE_API =
	"enhanced_kanban_view.api.kanban_board_rule.get_additional_fields";

const recent_validations = new Map();

function current_page() {
	const view = window.cur_list;
	const page = view && (view._kanban || view);
	return page && page.current_board ? page : null;
}

async function required_fields_for(board_name, column_name) {
	if (!board_name || !column_name) return [];
	try {
		const fields = await frappe.xcall(ENHANCED_RULE_API, {
			kanban_board_name: board_name,
			column_name,
		});
		return Array.isArray(fields) ? fields : [];
	} catch (error) {
		console.error("Enhanced Kanban: could not load column rules", error);
		return [];
	}
}

function values_for_column(page, column_id) {
	const values = { [page.field_name]: column_id };
	(page.get_effective_filters ? page.get_effective_filters() : []).forEach((f) => {
		if (f[2] === "=") values[f[1]] = f[3];
	});
	return values;
}

function refresh_board(page) {
	if (!page) return;
	if (page.board && page.board.refresh) page.board.refresh();
	(page.boards || []).forEach((group) => {
		if (group.board && group.board.refresh) group.board.refresh();
	});
}

async function dialog_doc(doctype, docname, values) {
	await frappe.model.with_doctype(doctype);
	const doc = docname
		? await frappe.db.get_doc(doctype, docname)
		: frappe.model.get_new_doc(doctype, null, null, true);
	// Fields that are not in the dialog still have to be persisted.
	Object.assign(doc, values);
	return doc;
}

async function rule_dialog(doctype, docname, fields, values) {
	if (!fields.length) return { saved: true };

	const doc = await dialog_doc(doctype, docname, values);
	const missing = fields.filter((f) => doc[f] === null || doc[f] === undefined || doc[f] === "");
	if (!missing.length) return { saved: true };

	const form = await frappe.ui.form.make_enhanced_kanban_quick_entry(
		doctype,
		null,
		null,
		doc,
		true, // force the dialog even when the DocType has quick_entry disabled
		missing,
		values
	);
	return form.wait_for_close();
}

/** Veto a drag when the target column has required fields that were not filled. */
async function before_card_move(move) {
	const page = current_page();
	if (!page || !move || !move.toColumn || move.toColumn === move.fromColumn) return true;

	// applyMoveMultiple calls this once per card with the same cardIds list.
	const card_ids = move.cardIds && move.cardIds.length > 1 ? move.cardIds : [move.cardId];
	const key = `${page.current_board}|${card_ids.join(",")}|${move.fromColumn}|${move.toColumn}`;
	for (const [saved_key, ts] of recent_validations) {
		if (Date.now() - ts > 10000) recent_validations.delete(saved_key);
	}
	const last = recent_validations.get(key);
	if (last && Date.now() - last < 10000) return true;

	const fields = await required_fields_for(page.current_board, move.toColumn);
	if (fields.length) {
		const values = { [page.field_name]: move.toColumn };
		if (card_ids.length > 1) {
			// Bulk drags cannot be edited one dialog at a time: ask once and veto
			// the whole drag when any selected card is incomplete.
			const docs = await frappe.db.get_list(page.doctype, {
				filters: { name: ["in", card_ids] },
				fields: ["name", ...fields],
				limit_page_length: 0,
			});
			const incomplete = docs.filter((doc) =>
				fields.some((f) => doc[f] === null || doc[f] === undefined || doc[f] === "")
			);
			if (incomplete.length) {
				frappe.msgprint({
					title: __("Required fields missing"),
					message: __("Fill the required fields before moving these cards: {0}", [
						incomplete.map((doc) => doc.name).join(", "),
					]),
					indicator: "orange",
				});
				return false;
			}
		} else {
			const result = await rule_dialog(page.doctype, move.cardId, fields, values);
			if (!result.saved) return false;
		}
	}

	recent_validations.set(key, Date.now());
	return true;
}

/** Replace the inline add-card input with a validated quick entry dialog. */
async function add_card(column_id) {
	const page = current_page();
	if (!page) return;

	const values = values_for_column(page, column_id);
	if (frappe.create_routes && frappe.create_routes[page.doctype]) {
		frappe.route_options = { ...values };
		return frappe.new_doc(page.doctype, values);
	}

	const fields = await required_fields_for(page.current_board, column_id);
	const doc = await dialog_doc(page.doctype, null, values);
	frappe.route_options = { ...values };
	await frappe.ui.form.make_enhanced_kanban_quick_entry(
		page.doctype,
		() => refresh_board(page),
		null,
		doc,
		true,
		fields,
		values
	);
}

function settings_for() {
	return {
		__enhanced_settings: true,
		callbacks: {
			onAddCard: (column_id) => add_card(column_id),
			onBeforeCardMove: (move) => before_card_move(move),
		},
		card_context_menu: (card, page) => [
			{
				label: __("Create Kanban Board Rule"),
				onclick: () => {
					const active = page || current_page();
					frappe.new_doc("Kanban Board Rule", {
						kanban_board: active && active.current_board,
					});
				},
			},
		],
	};
}

/**
 * Apply the settings to every DocType: the registry is keyed by DocType and we
 * cannot know in advance which boards an administrator will configure.
 * A Proxy keeps settings registered by other apps intact.
 */
function install_settings() {
	if (!frappe.kanban_v2 || !frappe.kanban_v2.settings) return false;
	if (frappe.kanban_v2.settings.__enhanced_kanban) return true;

	const base = frappe.kanban_v2.settings;
	const proxy = new Proxy(base, {
		get(target, key, receiver) {
			const value = Reflect.get(target, key, receiver);
			if (typeof key !== "string" || key.startsWith("__")) return value;
			if (!value) return settings_for();
			if (typeof value !== "object" || value.__enhanced_settings) return value;

			const ours = settings_for();
			return {
				...ours,
				...value,
				callbacks: { ...ours.callbacks, ...(value.callbacks || {}) },
				card_context_menu: (...args) => [
					...ours.card_context_menu(...args),
					...(typeof value.card_context_menu === "function"
						? value.card_context_menu(...args) || []
						: []),
				],
			};
		},
	});

	proxy.__enhanced_kanban = 1;
	frappe.kanban_v2.settings = proxy;
	return true;
}

// Only the registry is needed, not the on-demand Kanban bundle. Create it if a
// Frappe version without Kanban v2 (v15) is loaded: the proxy is harmless there
// and avoids polling for a registry that will never appear.
frappe.provide("frappe.kanban_v2");
frappe.provide("frappe.kanban_v2.settings");
install_settings();
