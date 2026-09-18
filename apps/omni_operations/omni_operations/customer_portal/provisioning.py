import frappe
from frappe.exceptions import TimestampMismatchError

from omni_operations.omni_security.access import INTERNAL_ROLES


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


def _portal_customers(email):
	return frappe.get_all(
		"Portal User",
		filters={"user": email},
		pluck="parent",
		distinct=True,
		order_by="parent asc",
	)


@frappe.whitelist()
def create_customer_portal_user(customer, email, full_name=None, phone=None, send_welcome_email=1, reassign=0):
	if not frappe.has_permission("Customer", "write"):
		frappe.throw("Not permitted to provision customer portal users.", frappe.PermissionError)
	if not frappe.db.exists("Customer", customer):
		frappe.throw(f"Customer not found: {customer}")

	email = (email or "").strip().lower()
	if not email:
		frappe.throw("Email is required for a customer portal user.")

	existing_customers = [name for name in _portal_customers(email) if name != customer]
	if existing_customers and not int(reassign or 0):
		frappe.throw(
			f"{email} is already linked to {', '.join(existing_customers)}. "
			"Use Reassign only after confirming that the previous customer access should be removed."
		)
	if existing_customers:
		for existing_customer in existing_customers:
			existing_doc = frappe.get_doc("Customer", existing_customer)
			existing_doc.set("portal_users", [row for row in existing_doc.portal_users if row.user != email])
			existing_doc.save(ignore_permissions=True)

	first_name, last_name = _split_name(full_name or email.split("@", 1)[0])
	created = False
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
		internal_roles = sorted(set(role.role for role in user.roles).intersection(INTERNAL_ROLES))
		if internal_roles:
			frappe.throw(
				f"{email} is an internal Omni user ({', '.join(internal_roles)}) and cannot be converted "
				"to a customer portal account. Use a separate customer email address."
			)
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
	return {
		"user": email,
		"customer": customer,
		"contact": contact,
		"created": created,
		"reassigned_from": existing_customers,
	}


@frappe.whitelist()
def get_customer_portal_users(customer):
	if not frappe.has_permission("Customer", "read"):
		frappe.throw("Not permitted to view customer portal users.", frappe.PermissionError)
	users = []
	for email in _portal_customers_for_customer(customer):
		user = frappe.db.get_value(
			"User", email, ["name", "full_name", "enabled", "user_type", "last_login"], as_dict=True
		)
		if user:
			users.append(user)
	return {"customer": customer, "users": users}


def _portal_customers_for_customer(customer):
	return frappe.get_all("Portal User", filters={"parent": customer}, pluck="user", order_by="user asc")


@frappe.whitelist()
def revoke_customer_portal_user(customer, email, disable_user=0):
	if not frappe.has_permission("Customer", "write"):
		frappe.throw("Not permitted to revoke customer portal users.", frappe.PermissionError)
	email = (email or "").strip().lower()
	customer_doc = frappe.get_doc("Customer", customer)
	before = len(customer_doc.portal_users)
	customer_doc.set("portal_users", [row for row in customer_doc.portal_users if row.user != email])
	if len(customer_doc.portal_users) != before:
		customer_doc.save(ignore_permissions=True)
	if int(disable_user or 0) and frappe.db.exists("User", email) and not _portal_customers(email):
		frappe.db.set_value("User", email, "enabled", 0, update_modified=True)
	frappe.db.commit()
	return {"user": email, "customer": customer, "revoked": before != len(customer_doc.portal_users)}


@frappe.whitelist()
def send_portal_password_reset(customer, email):
	if not frappe.has_permission("Customer", "write"):
		frappe.throw("Not permitted to manage customer portal users.", frappe.PermissionError)
	email = (email or "").strip().lower()
	if customer not in _portal_customers(email):
		frappe.throw(f"{email} is not linked to {customer}.")
	user = frappe.get_doc("User", email)
	if not user.enabled:
		frappe.throw("Enable this portal user before sending a password reset email.")
	from frappe.core.doctype.user.user import reset_password

	reset_password(email)
	return {"user": email, "sent": True}


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
