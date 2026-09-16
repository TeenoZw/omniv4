import frappe


QUOTE_ADD_ONS = [
	{
		"add_on_id": "fuel_monitoring_solutions",
		"display_name": "Fuel monitoring solutions",
		"status": "Available",
		"is_enabled": 1,
		"sort_order": 10,
		"public_note": "Quoted after assessment.",
	},
	{
		"add_on_id": "driver_ibuttons",
		"display_name": "Driver iButtons & Readers",
		"status": "Available",
		"is_enabled": 1,
		"sort_order": 20,
		"public_note": "Requires Professional tracker with 1-Wire support.",
	},
	{
		"add_on_id": "teltonika_dash_cam",
		"display_name": "Dash Cams",
		"status": "Out of Stock",
		"is_enabled": 0,
		"sort_order": 30,
		"public_note": "Out of stock. Dash cam installations are not available in the current quote workflow.",
	},
	{
		"add_on_id": "dash_cam_remote_monitoring",
		"display_name": "Remote dash cam monitoring",
		"status": "Out of Stock",
		"is_enabled": 0,
		"sort_order": 40,
		"public_note": "Out of stock. Remote dash cam monitoring will be enabled when dash cam support is available.",
	},
]


def sync_quote_add_ons():
	if not frappe.db.exists("DocType", "Omni Quote Add-on"):
		return

	for row in QUOTE_ADD_ONS:
		if frappe.db.exists("Omni Quote Add-on", row["add_on_id"]):
			doc = frappe.get_doc("Omni Quote Add-on", row["add_on_id"])
			for field in ("display_name", "sort_order"):
				doc.set(field, row[field])
			if not doc.public_note:
				doc.public_note = row["public_note"]
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc({"doctype": "Omni Quote Add-on", **row})
			doc.insert(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def get_public_quote_add_ons():
	if not frappe.db.exists("DocType", "Omni Quote Add-on"):
		return {"add_ons": []}

	rows = frappe.get_all(
		"Omni Quote Add-on",
		fields=["add_on_id", "display_name", "status", "is_enabled", "public_note", "sort_order"],
		order_by="sort_order asc, display_name asc",
		ignore_permissions=True,
	)
	return {
		"add_ons": [
			{
				"add_on_id": row.add_on_id,
				"display_name": row.display_name,
				"status": row.status,
				"is_enabled": bool(row.is_enabled),
				"public_note": row.public_note,
			}
			for row in rows
		]
	}
