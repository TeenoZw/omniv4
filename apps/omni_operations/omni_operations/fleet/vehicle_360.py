import frappe

from omni_operations.field_service.maintenance import get_vehicle_maintenance_status
from omni_operations.telematics.status import get_vehicle_telematics_status


@frappe.whitelist()
def get_vehicle_360(vehicle):
	doc = frappe.get_doc("Fleet Vehicle", vehicle)
	customer_profile = frappe.db.get_value("Customer Fleet Profile", doc.customer, "name")
	hub_assignment = frappe.get_all(
		"Vehicle Assignment",
		filters={"vehicle": vehicle, "status": "Active"},
		fields=["name", "customer", "start_datetime"],
		order_by="start_datetime desc",
		limit=1,
	)
	tracker = frappe.get_all(
		"Tracker Profile",
		filters={"current_vehicle": vehicle},
		fields=["name", "status", "imei", "tracker_name"],
		order_by="modified desc",
		limit=1,
	)
	sim = frappe.get_all(
		"SIM Profile",
		filters={"current_vehicle": vehicle},
		fields=["name", "status", "msisdn", "carrier"],
		order_by="modified desc",
		limit=1,
	)
	latest_invoice = frappe.get_all(
		"Sales Invoice",
		filters={"customer": doc.customer, "docstatus": 1},
		fields=["name", "status", "grand_total", "outstanding_amount"],
		order_by="posting_date desc, creation desc",
		limit=1,
	)
	installations = frappe.get_all(
		"Tracker Installation",
		filters={"vehicle": vehicle},
		fields=["name", "status", "tracker", "sim", "completed_date", "installation_location"],
		order_by="completed_date desc, modified desc",
		limit=5,
	)

	return {
		"vehicle": {
			"name": doc.name,
			"registration_number": doc.registration_number,
			"vehicle_name": doc.vehicle_name,
			"status": doc.status,
			"vehicle_type": doc.vehicle_type,
			"make": doc.make,
			"model": doc.model,
			"year": doc.year,
			"vin": doc.vin,
			"odometer": doc.odometer,
		},
		"customer": doc.customer,
		"customer_fleet_profile": customer_profile,
		"hub_assignment": hub_assignment[0] if hub_assignment else None,
		"tracker": tracker[0] if tracker else None,
		"sim": sim[0] if sim else None,
		"installations": installations,
		"latest_invoice": latest_invoice[0] if latest_invoice else None,
		"telematics": get_vehicle_telematics_status(vehicle),
		"maintenance": get_vehicle_maintenance_status(vehicle),
	}
