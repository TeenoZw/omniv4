import json

import frappe


OMNI_WORKSPACE = "Omni Operations"

OMNI_ROLES = [
	"System Manager",
	"Omni Operations Admin",
	"Fleet Manager",
	"Installation Coordinator",
	"Technician",
]

OMNI_SHORTCUTS = [
	("Website Enquiries", "Omni Onboarding Job", "Red", {"source": "Website", "status": "Qualification"}),
	("New Client Onboarding", "Omni Onboarding Job", "Cyan", None),
	("Prepare Tracker/SIM Kit", "Tracker SIM Assignment", "Orange", None),
	("Installation Queue", "Tracker Installation", "Orange", None),
	("Customer Fleets", "Customer Fleet Profile", "Blue", None),
	("Invoices", "Sales Invoice", "Purple", None),
	("Support Queue", "Issue", "Red", None),
]

OMNI_LINK_GROUPS = [
	(
		"Role Work Queues",
		[
			("Director Dashboard", "Customer Fleet Profile"),
			("Operations Admin Queue", "Omni Onboarding Job"),
			("Installation Coordinator Queue", "Tracker Installation"),
			("Fleet Manager Queue", "Fleet Maintenance Work Order"),
			("Technician Queue", "Tracker SIM Assignment"),
		],
	),
	(
		"1. New Customer",
		[
			("Leads", "Lead"),
			("Opportunities", "Opportunity"),
			("Quotations", "Quotation"),
			("Onboarding Jobs", "Omni Onboarding Job"),
		],
	),
	(
		"2. Customer Setup",
		[
			("Customers / Hubs", "Customer"),
			("Customer Fleet Profiles", "Customer Fleet Profile"),
			("Vehicles", "Fleet Vehicle"),
			("Drivers", "Fleet Driver"),
			("Portal Users", "User"),
		],
	),
	(
		"3. Inventory and Kit Prep",
		[
			("Trackers", "Tracker Profile"),
			("SIMs", "SIM Profile"),
			("Tracker/SIM Assignments", "Tracker SIM Assignment"),
			("Warehouses", "Warehouse"),
			("Stock Movements", "Stock Entry"),
		],
	),
	(
		"4. Installation and Field Work",
		[
			("Installation Queue", "Tracker Installation"),
			("Vehicle Assignments", "Vehicle Assignment"),
			("Maintenance Work Orders", "Fleet Maintenance Work Order"),
			("Fleet Documents", "Fleet Document"),
		],
	),
	(
		"5. Telematics",
		[
			("Provider Accounts", "Telematics Provider Account"),
			("Discovered Accounts", "Telematics Discovered Account"),
			("Discovered Users", "Telematics Discovered User"),
			("Unit Links", "Telematics Unit Link"),
			("Sync Logs", "Telematics Sync Log"),
		],
	),
	(
		"6. Billing and Customer Care",
		[
			("Quotations", "Quotation"),
			("Sales Orders", "Sales Order"),
			("Invoices", "Sales Invoice"),
			("Payments", "Payment Entry"),
			("Contracts", "Fleet Contract"),
			("Support Tickets", "Issue"),
		],
	),
	(
		"7. Purchasing and Stock Control",
		[
			("Items", "Item"),
			("Serial Numbers", "Serial No"),
			("Suppliers", "Supplier"),
			("Purchase Requests", "Material Request"),
			("RFQs", "Request for Quotation"),
			("Purchase Orders", "Purchase Order"),
			("Goods Receipts", "Purchase Receipt"),
			("Supplier Bills", "Purchase Invoice"),
		],
	),
	(
		"8. Fiscalisation",
		[
			("Fiscal Provider Accounts", "Fiscal Provider Account"),
			("Fiscal Devices", "Fiscal Device"),
			("Fiscal Days", "Fiscal Day"),
			("Fiscal Documents", "Fiscal Document"),
			("Fiscal Sync Logs", "Fiscal Sync Log"),
		],
	),
	(
		"9. Administration",
		[
			("Users", "User"),
			("Roles", "Role"),
			("Quote Add-ons", "Omni Quote Add-on"),
			("Company", "Company"),
			("System Settings", "System Settings"),
		],
	),
]


@frappe.whitelist()
def configure_omni_focused_desk():
	ensure_omni_workspace()
	hide_non_omni_workspaces()
	focus_administrator_on_omni()
	frappe.clear_cache()
	return {
		"default_workspace": frappe.db.get_value("User", "Administrator", "default_workspace"),
		"visible_workspaces": frappe.get_all(
			"Workspace",
			filters={"is_hidden": 0, "public": 1},
			pluck="name",
			order_by="sequence_id asc",
		),
	}


@frappe.whitelist()
def get_omni_workspace_sidebar_items():
	from frappe.desk.desktop import get_workspace_sidebar_items as get_default_workspace_sidebar_items

	if not _should_use_omni_sidebar():
		return get_default_workspace_sidebar_items()

	page = frappe.get_doc("Workspace", OMNI_WORKSPACE).as_dict()
	page["label"] = OMNI_WORKSPACE
	return {
		"pages": [page],
		"has_access": "Workspace Manager" in frappe.get_roles(),
		"has_create_access": frappe.has_permission(doctype="Workspace", ptype="create"),
	}


def ensure_omni_workspace():
	if frappe.db.exists("Workspace", OMNI_WORKSPACE):
		workspace = frappe.get_doc("Workspace", OMNI_WORKSPACE)
	else:
		workspace = frappe.new_doc("Workspace")
		workspace.name = OMNI_WORKSPACE
		workspace.label = OMNI_WORKSPACE
		workspace.title = OMNI_WORKSPACE

	workspace.label = OMNI_WORKSPACE
	workspace.title = OMNI_WORKSPACE
	workspace.module = "Omni Operations"
	workspace.public = 1
	workspace.is_hidden = 0
	workspace.sequence_id = 0
	workspace.icon = "organization"
	workspace.indicator_color = "blue"
	workspace.content = json.dumps(_workspace_content())

	workspace.set("shortcuts", [])
	for label, doctype, color, stats_filter in OMNI_SHORTCUTS:
		if frappe.db.exists("DocType", doctype):
			workspace.append(
				"shortcuts",
				{
					"type": "DocType",
					"label": label,
					"link_to": doctype,
					"doc_view": "List",
					"color": color,
					"stats_filter": json.dumps(stats_filter) if stats_filter else None,
				},
			)

	workspace.set("links", [])
	for group, links in OMNI_LINK_GROUPS:
		workspace.append("links", {"type": "Card Break", "label": group, "link_type": "DocType"})
		for label, doctype in links:
			if frappe.db.exists("DocType", doctype):
				workspace.append(
					"links",
					{
						"type": "Link",
						"label": label,
						"link_type": "DocType",
						"link_to": doctype,
						"onboard": 1,
					},
				)

	workspace.set("roles", [])
	for role in OMNI_ROLES:
		if frappe.db.exists("Role", role):
			workspace.append("roles", {"role": role})

	workspace.save(ignore_permissions=True)


def hide_non_omni_workspaces():
	for workspace_name in frappe.get_all("Workspace", pluck="name"):
		if workspace_name == OMNI_WORKSPACE:
			continue
		frappe.db.set_value("Workspace", workspace_name, "is_hidden", 1, update_modified=False)

	frappe.db.set_value("Workspace", OMNI_WORKSPACE, {"is_hidden": 0, "sequence_id": 0}, update_modified=False)


def focus_administrator_on_omni():
	if frappe.db.exists("User", "Administrator"):
		try:
			frappe.db.set_value("User", "Administrator", "default_workspace", OMNI_WORKSPACE)
			admin = frappe.get_doc("User", "Administrator")
			if "Workspace Manager" in {row.role for row in admin.roles}:
				admin.set("roles", [row for row in admin.roles if row.role != "Workspace Manager"])
				admin.save(ignore_permissions=True)
		except frappe.QueryDeadlockError:
			frappe.log_error(
				"Could not update Administrator default workspace because the User row changed during setup.",
				"Omni Desk Setup",
			)


def _workspace_content():
	content = [
		{
			"id": "omni_header_shortcuts",
			"type": "header",
			"data": {
				"text": "<span class=\"h4\"><b>Omni Command Center</b></span><br><span class=\"text-muted\">Use the shortcuts below for daily work. Start with New Client Onboarding unless you are receiving stock, preparing a kit, completing an installation, billing, or handling support.</span>",
				"col": 12,
			},
		},
		{
			"id": "omni_header_lifecycle",
			"type": "header",
			"data": {
				"text": (
					"<span class=\"h4\"><b>What Happens First?</b></span><br>"
					"<span class=\"text-muted\">"
					"1. Stock trackers and SIMs in Kwekwe or Hwange &nbsp;→&nbsp; "
					"2. Onboard customer hub &nbsp;→&nbsp; "
					"3. Capture vehicles &nbsp;→&nbsp; "
					"4. Prepare or reserve tracker/SIM kit &nbsp;→&nbsp; "
					"5. Schedule and complete installation &nbsp;→&nbsp; "
					"6. Link telematics &nbsp;→&nbsp; "
					"7. Invoice, support, documents and maintenance."
					"</span>"
				),
				"col": 12,
			},
		},
	]
	content.extend(
		{
			"id": f"omni_short_{label.lower().replace(' ', '_')}",
			"type": "shortcut",
			"data": {"shortcut_name": label, "col": 4},
		}
		for label, _doctype, _color, _stats_filter in OMNI_SHORTCUTS
	)
	content.append({"id": "omni_spacer", "type": "spacer", "data": {"col": 12}})
	content.append(
		{
			"id": "omni_header_work",
			"type": "header",
			"data": {
				"text": "<span class=\"h4\"><b>Work Areas and Role Queues</b></span><br><span class=\"text-muted\">Start in Role Work Queues, then move through the numbered workflow areas. Directors review the whole operation; coordinators schedule installs; technicians complete assigned field work; fleet managers monitor vehicles, documents, maintenance and customer health.</span>",
				"col": 12,
			},
		}
	)
	content.extend(
		{
			"id": f"omni_card_{group.lower().replace(' ', '_').replace('&', 'and')}",
			"type": "card",
			"data": {"card_name": group, "col": 4},
		}
		for group, _links in OMNI_LINK_GROUPS
	)
	return content


def _should_use_omni_sidebar():
	if frappe.session.user in {"Guest"}:
		return False

	roles = set(frappe.get_roles())
	return bool(
		{
			"Administrator",
			"System Manager",
			"Omni Operations Admin",
			"Fleet Manager",
			"Installation Coordinator",
			"Technician",
		}.intersection(roles)
	)
