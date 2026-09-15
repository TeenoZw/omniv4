import frappe


ROLE_QUEUE_DEFINITIONS = {
	"Omni Operations Admin": [
		("New Leads", "Lead", {"status": ["not in", ["Converted", "Do Not Contact"]]}),
		("Active Onboarding", "Omni Onboarding Job", {"status": ["not in", ["Completed", "Cancelled"]]}),
		("Open Support", "Issue", {"status": ["not in", ["Closed", "Resolved"]]}),
		("Unlinked Telematics Units", "Telematics Unit Link", {"vehicle": ["is", "not set"]}),
	],
	"Fleet Manager": [
		("Active Fleet Profiles", "Customer Fleet Profile", {"status": ["!=", "Inactive"]}),
		("Vehicles Needing Attention", "Fleet Vehicle", {"status": ["not in", ["Active", "Available"]]}),
		("Open Maintenance", "Fleet Maintenance Work Order", {"status": ["not in", ["Completed", "Cancelled"]]}),
		("Expiring Documents", "Fleet Document", {"status": ["not in", ["Archived", "Expired"]]}),
	],
	"Installation Coordinator": [
		("Onboarding Ready for Install", "Omni Onboarding Job", {"status": ["not in", ["Completed", "Cancelled"]]}),
		("Prepared Tracker/SIM Kits", "Tracker SIM Assignment", {"status": ["in", ["Prepared", "Reserved", "Assigned"]]}),
		("Scheduled Installations", "Tracker Installation", {"status": ["in", ["Scheduled", "In Progress"]]}),
		("Installations Needing Review", "Tracker Installation", {"status": ["in", ["Completed", "Needs Review"]]}),
	],
	"Technician": [
		("My Open Installations", "Tracker Installation", {"status": ["in", ["Scheduled", "In Progress"]]}),
		("Prepared Kits", "Tracker SIM Assignment", {"status": ["in", ["Prepared", "Reserved", "Assigned"]]}),
		("Open Maintenance", "Fleet Maintenance Work Order", {"status": ["not in", ["Completed", "Cancelled"]]}),
	],
}

DIRECTOR_QUEUES = [
	("Open Onboarding", "Omni Onboarding Job", {"status": ["not in", ["Completed", "Cancelled"]]}),
	("Open Support", "Issue", {"status": ["not in", ["Closed", "Resolved"]]}),
	("Overdue Contracts", "Fleet Contract", {"billing_status": "Overdue"}),
	("Unfiscalised Invoices", "Fiscal Document", {"status": ["in", ["Queued", "Failed", "Pending"]]}),
]


@frappe.whitelist()
def get_my_work_queues():
	roles = set(frappe.get_roles())
	queue_defs = []

	if roles.intersection({"System Manager", "Omni Operations Admin"}):
		queue_defs.extend(DIRECTOR_QUEUES)
		queue_defs.extend(ROLE_QUEUE_DEFINITIONS["Omni Operations Admin"])
	for role, definitions in ROLE_QUEUE_DEFINITIONS.items():
		if role in roles and role != "Omni Operations Admin":
			queue_defs.extend(definitions)

	seen = set()
	queues = []
	for label, doctype, filters in queue_defs:
		key = (label, doctype)
		if key in seen or not frappe.db.exists("DocType", doctype):
			continue
		seen.add(key)
		try:
			count = frappe.db.count(doctype, filters)
		except Exception:
			count = 0
		queues.append(
			{
				"label": label,
				"doctype": doctype,
				"count": count,
				"filters": filters,
				"route": f"/app/{frappe.scrub(doctype).replace('_', '-')}",
			}
		)

	return {"queues": queues}
