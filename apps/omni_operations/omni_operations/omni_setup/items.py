import frappe


FLEET_SERVICE_ITEMS = [
	{
		"item_code": "FLEET-MONTHLY-SERVICE",
		"item_name": "Fleet Monthly Service",
		"stock_uom": "Nos",
		"is_stock_item": 0,
		"item_group": "Services",
	},
	{
		"item_code": "TRACKER-HW-4G",
		"item_name": "4G GPS Tracker Hardware",
		"stock_uom": "Nos",
		"is_stock_item": 1,
		"item_group": "Products",
	},
	{
		"item_code": "SIM-IOT",
		"item_name": "IoT SIM Card",
		"stock_uom": "Nos",
		"is_stock_item": 1,
		"item_group": "Products",
	},
	{
		"item_code": "INSTALL-LABOUR",
		"item_name": "Tracker Installation Labour",
		"stock_uom": "Nos",
		"is_stock_item": 0,
		"item_group": "Services",
	},
	{
		"item_code": "MAINT-LABOUR",
		"item_name": "Fleet Maintenance Labour",
		"stock_uom": "Nos",
		"is_stock_item": 0,
		"item_group": "Services",
	},
]


@frappe.whitelist()
def ensure_fleet_service_items():
	created = []
	updated = []

	for item_spec in FLEET_SERVICE_ITEMS:
		item_code = item_spec["item_code"]
		if frappe.db.exists("Item", item_code):
			item = frappe.get_doc("Item", item_code)
			for fieldname, value in item_spec.items():
				if item.get(fieldname) != value:
					item.set(fieldname, value)
			item.save(ignore_permissions=True)
			updated.append(item_code)
		else:
			frappe.get_doc({"doctype": "Item", **item_spec}).insert(ignore_permissions=True)
			created.append(item_code)

	frappe.db.commit()
	return {"created": created, "updated": updated}
