app_name = "omni_operations"
app_title = "Omni Operations"
app_publisher = "TeenoZw"
app_description = "Fleet, telematics, tracker, SIM, maintenance, and customer operations for Omni Business Platform."
app_email = "admin@omni.local"
app_license = "gpl-3.0"
app_logo_url = "/assets/omni_operations/omni-logo.png"

fixtures = [
	{
		"doctype": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					"Omni Operations Admin",
					"Installation Coordinator",
					"Technician",
					"Fleet Manager",
					"Customer Portal User",
				],
			]
		],
	},
	{
		"doctype": "Module Def",
		"filters": [["app_name", "=", "omni_operations"]],
	},
	{
		"doctype": "Workspace",
		"filters": [["name", "=", "Omni Operations"]],
	},
	{
		"doctype": "Print Format",
		"filters": [["name", "=", "Omni Fiscal Sales Invoice"]],
	},
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "omni_operations",
# 		"logo": "/assets/omni_operations/logo.png",
# 		"title": "Omni Operations",
# 		"route": "/omni_operations",
# 		"has_permission": "omni_operations.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/omni_operations/css/omni_v3_bridge.css"
# app_include_js = "/assets/omni_operations/js/omni_operations.js"

# include js, css files in header of web template
web_include_css = "/assets/omni_operations/css/omni_v3_bridge.css"
# web_include_js = "/assets/omni_operations/js/omni_operations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "omni_operations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Customer": "public/js/customer.js",
	"Omni Onboarding Job": "public/js/omni_onboarding_job.js",
	"Fleet Vehicle": "public/js/fleet_vehicle.js",
	"Customer Fleet Profile": "public/js/customer_fleet_profile.js",
	"Tracker Installation": "public/js/tracker_installation.js",
	"Tracker SIM Assignment": "public/js/tracker_sim_assignment.js",
	"Tracker Profile": "public/js/tracker_profile.js",
	"SIM Profile": "public/js/sim_profile.js",
	"Telematics Discovered Account": "public/js/telematics_discovered_account.js",
}

doctype_list_js = {
	"Omni Onboarding Job": "public/js/omni_onboarding_job_list.js",
	"Customer Fleet Profile": "public/js/customer_fleet_profile_list.js",
	"Fleet Vehicle": "public/js/fleet_vehicle_list.js",
	"Tracker Installation": "public/js/tracker_installation_list.js",
	"Tracker SIM Assignment": "public/js/tracker_sim_assignment_list.js",
	"Fleet Maintenance Work Order": "public/js/fleet_maintenance_work_order_list.js",
	"Fleet Document": "public/js/fleet_document_list.js",
	"Fleet Contract": "public/js/fleet_contract_list.js",
	"Telematics Discovered Account": "public/js/telematics_discovered_account_list.js",
	"Telematics Discovered User": "public/js/telematics_discovered_user_list.js",
	"Telematics Unit Link": "public/js/telematics_unit_link_list.js",
}

website_route_rules = [
	{"from_route": "/portal", "to_route": "omni_customer_portal"},
	{"from_route": "/omni-customer-portal", "to_route": "omni_customer_portal"},
]

before_request = ["omni_operations.website_routing.before_request"]

doc_events = {
	"Sales Invoice": {
		"on_submit": "omni_operations.fiscalisation.events.on_sales_invoice_submit",
	},
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "omni_operations/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

get_website_user_home_page = "omni_operations.omni_security.access.role_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "omni_operations.utils.jinja_methods",
# 	"filters": "omni_operations.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "omni_operations.install.before_install"
after_install = "omni_operations.omni_setup.bootstrap.after_install"
after_migrate = "omni_operations.omni_setup.bootstrap.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "omni_operations.uninstall.before_uninstall"
# after_uninstall = "omni_operations.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "omni_operations.utils.before_app_install"
# after_app_install = "omni_operations.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "omni_operations.utils.before_app_uninstall"
# after_app_uninstall = "omni_operations.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

notification_config = "omni_operations.notifications.get_notification_config"

permission_query_conditions = {
	"Omni Onboarding Job": "omni_operations.omni_security.access.omni_onboarding_job_query",
	"Customer Fleet Profile": "omni_operations.omni_security.access.customer_fleet_profile_query",
	"Fleet Vehicle": "omni_operations.omni_security.access.fleet_vehicle_query",
	"Fleet Driver": "omni_operations.omni_security.access.fleet_driver_query",
	"Vehicle Assignment": "omni_operations.omni_security.access.vehicle_assignment_query",
	"Tracker Installation": "omni_operations.omni_security.access.tracker_installation_query",
	"Tracker SIM Assignment": "omni_operations.omni_security.access.tracker_sim_assignment_query",
	"Fleet Maintenance Work Order": "omni_operations.omni_security.access.fleet_maintenance_work_order_query",
	"Fleet Document": "omni_operations.omni_security.access.fleet_document_query",
	"Fleet Contract": "omni_operations.omni_security.access.fleet_contract_query",
	"Telematics Unit Link": "omni_operations.omni_security.access.telematics_unit_link_query",
	"Fiscal Document": "omni_operations.omni_security.access.fiscal_document_query",
	"Sales Invoice": "omni_operations.omni_security.access.sales_invoice_query",
	"Issue": "omni_operations.omni_security.access.issue_query",
}

override_whitelisted_methods = {
	"frappe.desk.desktop.get_workspace_sidebar_items": "omni_operations.omni_setup.desk.get_omni_workspace_sidebar_items",
}

has_permission = {
	"Omni Onboarding Job": "omni_operations.omni_security.access.has_customer_permission",
	"Customer Fleet Profile": "omni_operations.omni_security.access.has_customer_permission",
	"Fleet Vehicle": "omni_operations.omni_security.access.has_customer_permission",
	"Fleet Driver": "omni_operations.omni_security.access.has_customer_permission",
	"Vehicle Assignment": "omni_operations.omni_security.access.has_customer_permission",
	"Tracker Installation": "omni_operations.omni_security.access.has_customer_permission",
	"Tracker SIM Assignment": "omni_operations.omni_security.access.has_customer_permission",
	"Fleet Maintenance Work Order": "omni_operations.omni_security.access.has_customer_permission",
	"Fleet Document": "omni_operations.omni_security.access.has_customer_permission",
	"Fleet Contract": "omni_operations.omni_security.access.has_customer_permission",
	"Telematics Unit Link": "omni_operations.omni_security.access.has_customer_permission",
	"Fiscal Document": "omni_operations.omni_security.access.has_customer_permission",
	"Sales Invoice": "omni_operations.omni_security.access.has_customer_permission",
	"Issue": "omni_operations.omni_security.access.has_customer_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
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

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"omni_operations.telematics.scheduled.sync_enabled_provider_accounts",
	],
}

# Testing
# -------

# before_tests = "omni_operations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "omni_operations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "omni_operations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["omni_operations.utils.before_request"]
# after_request = ["omni_operations.utils.after_request"]

# Job Events
# ----------
# before_job = ["omni_operations.utils.before_job"]
# after_job = ["omni_operations.utils.after_job"]

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
# 	"omni_operations.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
