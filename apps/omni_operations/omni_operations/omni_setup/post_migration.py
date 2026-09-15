import re

import frappe


INTERNAL_EMAIL_DOMAINS = {"omnilogistics.co.zw", "omni.local", "example.com"}


def vehicle_type_for(vehicle):
	text = " ".join(
		[
			vehicle.get("vehicle_name") or "",
			vehicle.get("make") or "",
			vehicle.get("model") or "",
			vehicle.get("notes") or "",
		]
	).lower()

	if any(word in text for word in ["truck", "tgx", "ftr", "dutro", "hilux", "kb300"]):
		return "Truck"
	if any(word in text for word in ["x-trail", "xtrail", "note", "vezzel", "probo", "e320"]):
		return "Car"
	if "trailer" in text:
		return "Trailer"
	if "bus" in text:
		return "Bus"
	if "van" in text:
		return "Van"
	return vehicle.vehicle_type or "Other"


def clean_vehicle_key(vehicle):
	if not vehicle.name.startswith("asset-label-"):
		return vehicle.name

	base = vehicle.vehicle_name or vehicle.name.replace("asset-label-", "")
	base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").upper()
	customer = re.sub(r"[^A-Za-z0-9]+", "-", vehicle.customer or "").strip("-").upper()
	return f"{base}-{customer}" if customer else base


def rename_vehicle(old_name, new_name):
	if old_name == new_name:
		return old_name
	if frappe.db.exists("Fleet Vehicle", new_name):
		return new_name

	return frappe.rename_doc("Fleet Vehicle", old_name, new_name, force=True)


def cleanup_migrated_vehicles():
	renamed = []
	updated_types = []
	vehicles = frappe.get_all(
		"Fleet Vehicle",
		fields=["name", "vehicle_name", "customer", "vehicle_type", "make", "model", "notes"],
		limit=500,
	)
	for row in vehicles:
		doc = frappe.get_doc("Fleet Vehicle", row.name)
		target_type = vehicle_type_for(doc)
		if doc.vehicle_type != target_type:
			doc.vehicle_type = target_type
			doc.save(ignore_permissions=True)
			updated_types.append(doc.name)

		new_name = clean_vehicle_key(doc)
		if new_name != doc.name:
			old_name = doc.name
			actual = rename_vehicle(old_name, new_name)
			if actual != old_name:
				renamed.append({"old": old_name, "new": actual})

	return {"renamed": renamed, "updated_types": updated_types}


def customer_for_contact(contact):
	for link in contact.links:
		if link.link_doctype == "Customer" and link.link_name:
			return link.link_name
	return None


def should_skip_email(email):
	domain = email.split("@")[-1].lower() if "@" in email else ""
	return domain in INTERNAL_EMAIL_DOMAINS


def ensure_portal_user(email, full_name):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		created = False
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": full_name or email,
				"send_welcome_email": 0,
				"user_type": "Website User",
				"enabled": 0,
			}
		)
		user.insert(ignore_permissions=True)
		created = True

	if "Customer Portal User" not in [role.role for role in user.roles]:
		user.append("roles", {"role": "Customer Portal User"})
	if user.user_type != "Website User":
		user.user_type = "Website User"
	user.enabled = 0
	user.save(ignore_permissions=True)
	return user.name, created


def provision_customer_portal_users():
	created = []
	updated = []
	skipped = []
	contacts = frappe.get_all("Contact", fields=["name", "first_name"], limit=500)
	for contact_row in contacts:
		contact = frappe.get_doc("Contact", contact_row.name)
		customer = customer_for_contact(contact)
		if not customer:
			continue

		for email_row in contact.email_ids:
			email = (email_row.email_id or "").strip().lower()
			if not email or should_skip_email(email):
				skipped.append({"email": email, "reason": "internal_or_invalid"})
				continue

			user, was_created = ensure_portal_user(email, contact.first_name)
			if was_created:
				created.append({"user": user, "customer": customer})
			else:
				updated.append({"user": user, "customer": customer})

			customer_doc = frappe.get_doc("Customer", customer)
			if not any(portal_user.user == user for portal_user in customer_doc.portal_users):
				customer_doc.append("portal_users", {"user": user})
				customer_doc.save(ignore_permissions=True)

	return {"created": created, "updated": updated, "skipped": skipped}


def backfill_tracker_sim_assignments():
	if not frappe.db.exists("DocType", "Tracker SIM Assignment"):
		return {"created": [], "updated": [], "skipped": ["Tracker SIM Assignment DocType missing"]}

	from omni_operations.tracker_inventory.doctype.tracker_sim_assignment.tracker_sim_assignment import (
		upsert_assignment_from_installation,
	)

	created = []
	updated = []
	skipped = []

	for installation_name in frappe.get_all(
		"Tracker Installation",
		filters={"sim": ["is", "set"]},
		pluck="name",
		limit=1000,
	):
		before = set(frappe.get_all("Tracker SIM Assignment", pluck="name"))
		assignment = upsert_assignment_from_installation(frappe.get_doc("Tracker Installation", installation_name))
		if not assignment:
			skipped.append(installation_name)
			continue
		if assignment in before:
			updated.append(assignment)
		else:
			created.append(assignment)

	for sim in frappe.get_all(
		"SIM Profile",
		filters={"current_tracker": ["is", "set"]},
		fields=["name", "status", "current_tracker", "current_customer", "current_vehicle"],
		limit=1000,
	):
		if frappe.db.exists("Tracker SIM Assignment", {"sim": sim.name, "status": ["in", ["Prepared", "Reserved", "Assigned", "Installed"]]}):
			continue

		if not frappe.db.exists("Tracker Profile", sim.current_tracker):
			skipped.append(sim.name)
			continue

		if sim.status == "Installed" and sim.current_customer and sim.current_vehicle:
			status = "Installed"
		elif sim.status == "Assigned" and sim.current_customer and sim.current_vehicle:
			status = "Assigned"
		elif sim.status == "Reserved" and sim.current_customer:
			status = "Reserved"
		else:
			status = "Prepared"
		doc = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"naming_series": "TSA-.YYYY.-.####",
				"status": status,
				"slot": "Primary",
				"tracker": sim.current_tracker,
				"sim": sim.name,
				"customer": sim.current_customer,
				"vehicle": sim.current_vehicle,
				"notes": "Backfilled from SIM Profile current assignment fields.",
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)

	from omni_operations.tracker_inventory.doctype.tracker_sim_assignment.tracker_sim_assignment import (
		sync_all_tracker_sim_assignment_state,
	)

	sync_all_tracker_sim_assignment_state()
	return {"created": created, "updated": updated, "skipped": skipped}


@frappe.whitelist()
def run_post_migration_cleanup():
	result = {
		"vehicles": cleanup_migrated_vehicles(),
		"portal_users": provision_customer_portal_users(),
		"tracker_sim_assignments": backfill_tracker_sim_assignments(),
	}
	frappe.db.commit()
	return result
