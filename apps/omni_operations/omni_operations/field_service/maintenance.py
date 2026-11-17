import frappe

from omni_operations.omni_security.access import has_customer_permission


@frappe.whitelist()
def get_vehicle_maintenance_status(vehicle):
	vehicle_doc = frappe.get_doc("Fleet Vehicle", vehicle)
	if not vehicle_doc.has_permission("read") or not has_customer_permission(vehicle_doc, ptype="read"):
		frappe.throw("You are not permitted to view this vehicle.", frappe.PermissionError)

	work_orders = frappe.get_all(
		"Fleet Maintenance Work Order",
		filters={"vehicle": vehicle},
		fields=[
			"name",
			"status",
			"maintenance_type",
			"scheduled_date",
			"completed_date",
			"billing_status",
			"stock_entry",
			"sales_invoice",
			"total_amount",
		],
		order_by="completed_date desc, scheduled_date desc, creation desc",
		limit=5,
	)

	if not work_orders:
		return {
			"status": "No History",
			"indicator": "gray",
			"message": "No maintenance work orders",
			"open_count": 0,
			"latest": None,
			"work_orders": [],
		}

	open_count = frappe.db.count(
		"Fleet Maintenance Work Order",
		{"vehicle": vehicle, "status": ["in", ["Draft", "Scheduled", "In Progress"]]},
	)
	latest = work_orders[0]
	indicator = "green"
	if open_count:
		indicator = "orange"
	elif latest.status == "Cancelled":
		indicator = "gray"

	return {
		"status": f"{open_count} Open" if open_count else latest.status,
		"indicator": indicator,
		"message": f"{latest.name} - {latest.maintenance_type}",
		"open_count": open_count,
		"latest": latest,
		"work_orders": work_orders,
	}
