import frappe
from frappe.exceptions import TimestampMismatchError


def _split_name(full_name):
	full_name = (full_name or "Customer User").strip()
	parts = full_name.split(" ", 1)
	return parts[0], parts[1] if len(parts) > 1 else ""


def _ensure_contact_for_customer(customer, email=None, full_name=None, phone=None):
	email = (email or "").strip().lower()
	phone = (phone or "").strip()
	if not email and not phone:
		return None

	existing_contact = frappe.db.get_value("Contact Email", {"email_id": email}, "parent") if email else None
	if existing_contact:
		contact = frappe.get_doc("Contact", existing_contact)
	else:
		first_name, last_name = _split_name(full_name)
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": first_name,
				"last_name": last_name,
			}
		)

	def apply_updates():
		changed = False
		if email and not any(row.email_id == email for row in contact.email_ids):
			contact.append("email_ids", {"email_id": email, "is_primary": 1})
			changed = True
		if phone and not any(row.phone == phone for row in contact.phone_nos):
			contact.append("phone_nos", {"phone": phone, "is_primary_phone": 1})
			changed = True
		if not any(link.link_doctype == "Customer" and link.link_name == customer for link in contact.links):
			contact.append("links", {"link_doctype": "Customer", "link_name": customer})
			changed = True
		return changed

	changed = apply_updates()

	if contact.is_new():
		contact.insert(ignore_permissions=True)
	elif changed:
		try:
			contact.save(ignore_permissions=True)
		except TimestampMismatchError:
			contact.reload()
			if apply_updates():
				contact.save(ignore_permissions=True)
	return contact.name


@frappe.whitelist()
def create_customer_portal_user(customer, email, full_name=None, phone=None, send_welcome_email=1):
	if not frappe.has_permission("Customer", "write"):
		frappe.throw("Not permitted to provision customer portal users.", frappe.PermissionError)
	if not frappe.db.exists("Customer", customer):
		frappe.throw(f"Customer not found: {customer}")

	email = (email or "").strip().lower()
	if not email:
		frappe.throw("Email is required for a customer portal user.")

	first_name, last_name = _split_name(full_name or email.split("@", 1)[0])
	created = False
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
				"user_type": "Website User",
				"enabled": 1,
				"send_welcome_email": 1 if int(send_welcome_email or 0) else 0,
			}
		).insert(ignore_permissions=True)
		created = True

	user.enabled = 1
	user.user_type = "Website User"
	if full_name and not user.first_name:
		user.first_name = first_name
	if full_name and not user.last_name:
		user.last_name = last_name
	if "Customer Portal User" not in [role.role for role in user.roles]:
		user.append("roles", {"role": "Customer Portal User"})
	user.save(ignore_permissions=True)

	contact = _ensure_contact_for_customer(customer, email=email, full_name=full_name, phone=phone)
	customer_doc = frappe.get_doc("Customer", customer)
	if not any(portal_user.user == email for portal_user in customer_doc.portal_users):
		customer_doc.append("portal_users", {"user": email})
		customer_doc.save(ignore_permissions=True)

	frappe.db.commit()
	return {"user": email, "customer": customer, "contact": contact, "created": created}


@frappe.whitelist()
def ensure_internal_portal_test_user(customer="Mapanje Hub", email="portal-test@omni.local"):
	if not frappe.db.exists("Customer", customer):
		frappe.throw(f"Customer not found: {customer}")

	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		created = False
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Portal Test",
				"last_name": customer,
				"user_type": "Website User",
				"enabled": 1,
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		created = True

	if "Customer Portal User" not in [role.role for role in user.roles]:
		user.append("roles", {"role": "Customer Portal User"})
	user.enabled = 1
	user.user_type = "Website User"
	user.save(ignore_permissions=True)

	if not frappe.db.exists("Contact", f"Portal Test-{customer}"):
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Portal Test",
				"email_ids": [{"email_id": email, "is_primary": 1}],
				"links": [{"link_doctype": "Customer", "link_name": customer}],
			}
		).insert(ignore_permissions=True)
	else:
		contact = frappe.get_doc("Contact", f"Portal Test-{customer}")

	customer_doc = frappe.get_doc("Customer", customer)
	if not any(portal_user.user == email for portal_user in customer_doc.portal_users):
		customer_doc.append("portal_users", {"user": email})
		customer_doc.save(ignore_permissions=True)

	frappe.db.commit()
	return {"user": email, "customer": customer, "contact": contact.name, "created": created}
