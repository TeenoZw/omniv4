import frappe


@frappe.whitelist()
def merge_customer(source_customer, target_customer):
	"""Merge a duplicate Customer into the Customer selected to survive."""
	if source_customer == target_customer:
		frappe.throw("Choose a different customer to keep.")
	if not frappe.has_permission("Customer", "write") or not frappe.has_permission("Customer", "delete"):
		frappe.throw("You need write and delete permission on Customer to merge records.", frappe.PermissionError)
	if not frappe.db.exists("Customer", source_customer):
		frappe.throw(f"Customer {source_customer} does not exist.")
	if not frappe.db.exists("Customer", target_customer):
		frappe.throw(f"Customer {target_customer} does not exist.")

	portal_users = get_merged_portal_users(source_customer, target_customer)
	prepare_customer_fleet_profile_merge(source_customer, target_customer)

	from frappe.model.rename_doc import rename_doc

	rename_doc(
		"Customer",
		source_customer,
		target_customer,
		force=True,
		merge=True,
		ignore_permissions=True,
		show_alert=False,
	)
	restore_portal_users(target_customer, portal_users)
	frappe.db.commit()
	return {"source_customer": source_customer, "customer": target_customer, "merged": True}


def get_merged_portal_users(source_customer, target_customer):
	"""Capture portal access before Frappe merges the Customer child tables."""
	users = frappe.get_all(
		"Portal User",
		filters={"parent": ["in", [source_customer, target_customer]]},
		pluck="user",
	)
	return sorted(set(filter(None, users)))


def restore_portal_users(customer, users):
	if not users:
		return
	customer_doc = frappe.get_doc("Customer", customer)
	existing = {row.user for row in customer_doc.portal_users}
	for user in users:
		if user not in existing:
			customer_doc.append("portal_users", {"user": user})
	if {row.user for row in customer_doc.portal_users} != existing:
		customer_doc.save(ignore_permissions=True)


def prepare_customer_fleet_profile_merge(source_customer, target_customer):
	if not frappe.db.exists("DocType", "Customer Fleet Profile"):
		return
	source_profile_name = frappe.db.get_value("Customer Fleet Profile", {"customer": source_customer}, "name")
	if not source_profile_name:
		return
	target_profile_name = frappe.db.get_value("Customer Fleet Profile", {"customer": target_customer}, "name")
	if not target_profile_name:
		source_profile = frappe.get_doc("Customer Fleet Profile", source_profile_name)
		source_profile.customer = target_customer
		source_profile.save(ignore_permissions=True)
		if source_profile.name != target_customer:
			from frappe.model.rename_doc import rename_doc
			rename_doc(
				"Customer Fleet Profile", source_profile.name, target_customer,
				force=True, ignore_permissions=True, show_alert=False,
			)
		return

	source_profile = frappe.get_doc("Customer Fleet Profile", source_profile_name)
	target_profile = frappe.get_doc("Customer Fleet Profile", target_profile_name)
	for fieldname in (
		"account_manager", "primary_vehicle", "primary_tracker", "primary_sim", "primary_driver",
		"vehicle_assignment", "last_installation", "latest_sales_invoice", "latest_support_ticket",
	):
		if not target_profile.get(fieldname) and source_profile.get(fieldname):
			target_profile.set(fieldname, source_profile.get(fieldname))
	for fieldname in ("maintenance_notes", "contract_notes", "notes"):
		values = [value for value in (target_profile.get(fieldname), source_profile.get(fieldname)) if value]
		if values:
			target_profile.set(fieldname, "\n\n".join(dict.fromkeys(values)))
	target_profile.save(ignore_permissions=True)
	frappe.delete_doc("Customer Fleet Profile", source_profile.name, ignore_permissions=True, force=True)
