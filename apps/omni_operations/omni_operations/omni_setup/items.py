import frappe
from frappe import _
from frappe.utils.nestedset import get_root_of


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
	_ensure_item_prerequisites()

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


def _ensure_item_prerequisites():
	if not frappe.db.exists("UOM", "Nos"):
		frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)

	root_item_group = get_root_of("Item Group") or _("All Item Groups")
	if not frappe.db.exists("Item Group", root_item_group):
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": root_item_group,
				"is_group": 1,
				"parent_item_group": "",
			}
		).insert(ignore_permissions=True)

	for item_group in {item["item_group"] for item in FLEET_SERVICE_ITEMS}:
		if not frappe.db.exists("Item Group", item_group):
			frappe.get_doc(
				{
					"doctype": "Item Group",
					"item_group_name": item_group,
					"is_group": 0,
					"parent_item_group": root_item_group,
				}
			).insert(ignore_permissions=True)
