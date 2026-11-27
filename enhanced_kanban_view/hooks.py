app_name = "enhanced_kanban_view"
app_title = "Enhanced Kanban View"
app_publisher = "Ibrahim Aboelsoud"
app_description = "Kanban View based on Link field type"
app_email = "i.aboelsoud21@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "enhanced_kanban_view",
# 		"logo": "/assets/enhanced_kanban_view/logo.png",
# 		"title": "Enhanced Kanban View",
# 		"route": "/enhanced_kanban_view",
# 		"has_permission": "enhanced_kanban_view.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/enhanced_kanban_view/css/enhanced_kanban_view.css"

app_include_js = "enhanced_kanban_view.bundle.js"

# include js, css files in header of web template
# web_include_css = "/assets/enhanced_kanban_view/css/enhanced_kanban_view.css"
# web_include_js = "/assets/enhanced_kanban_view/js/enhanced_kanban_view.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "enhanced_kanban_view/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "enhanced_kanban_view/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "enhanced_kanban_view.utils.jinja_methods",
# 	"filters": "enhanced_kanban_view.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "enhanced_kanban_view.install.before_install"
# after_install = "enhanced_kanban_view.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "enhanced_kanban_view.uninstall.before_uninstall"
# after_uninstall = "enhanced_kanban_view.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "enhanced_kanban_view.utils.before_app_install"
# after_app_install = "enhanced_kanban_view.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "enhanced_kanban_view.utils.before_app_uninstall"
# after_app_uninstall = "enhanced_kanban_view.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "enhanced_kanban_view.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Kanban column rules must also be enforced server-side: the v2 engine saves
# cards through frappe.client.set_value / bulk_update, bypassing board methods.
doc_events = {
	"*": {
		"validate": "enhanced_kanban_view.kanban_rules.validate_kanban_rules",
	},
	"Kanban Board": {
		"on_update": "enhanced_kanban_view.kanban_rules.clear_rules_cache",
		"on_trash": "enhanced_kanban_view.kanban_rules.clear_rules_cache",
	},
	"Kanban Board Rule": {
		"on_update": "enhanced_kanban_view.kanban_rules.clear_rules_cache",
		"on_trash": "enhanced_kanban_view.kanban_rules.clear_rules_cache",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"enhanced_kanban_view.tasks.all"
# 	],
# 	"daily": [
# 		"enhanced_kanban_view.tasks.daily"
# 	],
# 	"hourly": [
# 		"enhanced_kanban_view.tasks.hourly"
# 	],
# 	"weekly": [
# 		"enhanced_kanban_view.tasks.weekly"
# 	],
# 	"monthly": [
# 		"enhanced_kanban_view.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "enhanced_kanban_view.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "enhanced_kanban_view.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "enhanced_kanban_view.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["enhanced_kanban_view.utils.before_request"]
# after_request = ["enhanced_kanban_view.utils.after_request"]

# Job Events
# ----------
# before_job = ["enhanced_kanban_view.utils.before_job"]
# after_job = ["enhanced_kanban_view.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"enhanced_kanban_view.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

