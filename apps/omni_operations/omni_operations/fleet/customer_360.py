import frappe


INTERNAL_ROLES = {
	"System Manager",
	"Omni Operations Admin",
	"Fleet Manager",
	"Installation Coordinator",
	"Technician",
}


@frappe.whitelist()
def get_customer_fleet_360(customer):
	validate_customer_access(customer)
	profile = frappe.get_doc("Customer Fleet Profile", customer)
	vehicles = frappe.get_all(
		"Fleet Vehicle",
		filters={"customer": customer},
		fields=["name", "vehicle_name", "status", "vehicle_type", "make", "model", "odometer"],
		order_by="modified desc",
		limit=20,
	)
	unit_links = frappe.get_all(
		"Telematics Unit Link",
		filters={"customer": customer},
		fields=[
			"name",
			"vehicle",
			"provider",
			"last_sync_status",
			"external_unit_name",
			"sync_enabled",
			"last_position_datetime",
			"speed",
			"ignition",
			"odometer",
		],
		order_by="modified desc",
		limit=20,
	)
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1},
		fields=["name", "posting_date", "due_date", "status", "grand_total", "outstanding_amount"],
		order_by="posting_date desc, creation desc",
		limit=5,
	)
	tickets = frappe.get_all(
		"Issue",
		filters={"customer": customer, "status": ["!=", "Closed"]},
		fields=["name", "status", "priority", "subject"],
		order_by="modified desc",
		limit=5,
	)
	maintenance = frappe.get_all(
		"Fleet Maintenance Work Order",
		filters={"customer": customer},
		fields=["name", "vehicle", "status", "billing_status", "scheduled_date", "completed_date", "total_amount"],
		order_by="modified desc",
		limit=5,
	)
	documents = frappe.get_all(
		"Fleet Document",
		filters={"customer": customer, "portal_visible": 1, "status": ["!=", "Archived"]},
		fields=["name", "title", "document_type", "status", "vehicle", "expiry_date", "attachment"],
		order_by="expiry_date asc, modified desc",
		limit=10,
	)
	contracts = frappe.get_all(
		"Fleet Contract",
		filters={"customer": customer, "portal_visible": 1, "status": ["not in", ["Cancelled"]]},
		fields=[
			"name",
			"contract_title",
			"status",
			"vehicle",
			"billing_frequency",
			"monthly_rate",
			"next_billing_date",
			"billing_status",
			"latest_sales_invoice",
		],
		order_by="status asc, next_billing_date asc, modified desc",
		limit=10,
	)
	links_by_vehicle = {link.vehicle: link for link in unit_links if link.vehicle}
	for vehicle in vehicles:
		link = links_by_vehicle.get(vehicle.name)
		if link:
			vehicle.telematics_label = "Live" if link.sync_enabled else "Sync Off"
			vehicle.telematics_status = link.last_sync_status or "Never Synced"
			vehicle.telematics_unit = link.external_unit_name or link.name
			vehicle.last_position_datetime = link.last_position_datetime
		else:
			vehicle.telematics_label = "Not Linked"
			vehicle.telematics_status = "Not Linked"
			vehicle.telematics_unit = None
			vehicle.last_position_datetime = None

	open_maintenance = [
		work_order
		for work_order in maintenance
		if work_order.status not in {"Completed", "Cancelled"}
	]
	outstanding_invoices = [invoice for invoice in invoices if invoice.outstanding_amount]
	live_telematics = [link for link in unit_links if link.sync_enabled]
	expiring_documents = [
		document for document in documents if document.expiry_date and document.status != "Expired"
	]
	active_contracts = [contract for contract in contracts if contract.status == "Active"]
	overdue_contracts = [contract for contract in contracts if contract.billing_status == "Overdue"]

	return {
		"profile": {
			"name": profile.name,
			"status": profile.status,
			"total_vehicles": profile.total_vehicles,
			"active_trackers": profile.active_trackers,
			"installed_sims": profile.installed_sims,
			"open_support_tickets": profile.open_support_tickets,
			"invoice_status": profile.invoice_status,
			"invoice_outstanding_amount": profile.invoice_outstanding_amount,
			"latest_sales_invoice": profile.latest_sales_invoice,
			"latest_payment_entry": profile.latest_payment_entry,
		},
		"summary": {
			"vehicle_count": frappe.db.count("Fleet Vehicle", {"customer": customer}),
			"tracker_count": profile.active_trackers or len(unit_links),
			"live_telematics_count": len(live_telematics),
			"staged_telematics_count": len(unit_links) - len(live_telematics),
			"open_maintenance_count": len(open_maintenance),
			"open_invoice_count": len(outstanding_invoices),
			"open_ticket_count": len(tickets),
			"portal_document_count": len(documents),
			"expiring_document_count": len(expiring_documents),
			"active_contract_count": len(active_contracts),
			"overdue_contract_count": len(overdue_contracts),
		},
		"vehicles": vehicles,
		"telematics": unit_links,
		"invoices": invoices,
		"support_tickets": tickets,
		"maintenance": maintenance,
		"documents": documents,
		"contracts": contracts,
	}


def validate_customer_access(customer):
	if frappe.session.user == "Administrator":
		return

	user_roles = set(frappe.get_roles(frappe.session.user))
	if user_roles.intersection(INTERNAL_ROLES):
		return

	linked_customer = get_customer_for_user(frappe.session.user)
	if linked_customer == customer:
		return

	frappe.throw("You do not have access to this customer.", frappe.PermissionError)


def get_customer_for_user(user):
	user_email = frappe.db.get_value("User", user, "email")
	if not user_email:
		return None

	contacts = frappe.get_all(
		"Contact Email",
		filters={"email_id": user_email},
		fields=["parent"],
		limit=50,
	)

	for contact in contacts:
		customer = frappe.db.get_value(
			"Dynamic Link",
			{
				"parent": contact.parent,
				"parenttype": "Contact",
				"link_doctype": "Customer",
			},
			"link_name",
		)
		if customer:
			return customer

	return None
