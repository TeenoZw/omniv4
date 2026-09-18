import frappe

from omni_operations.fleet.customer_360 import get_customer_fleet_360, get_customer_for_user
from omni_operations.fleet.vehicle_360 import get_vehicle_360
from omni_operations.omni_security.access import INTERNAL_ROLES, PORTAL_ROLE

CURRENT_TERMS_VERSION = "2026-09-01"
CURRENT_PRIVACY_POLICY_VERSION = "2026-09-15"
TERMS_URL = "/terms"
PRIVACY_POLICY_URL = "/privacy"


def _require_portal_user():
	if frappe.session.user == "Guest":
		frappe.throw("Please log in to access the customer portal.", frappe.PermissionError)


def _is_internal_user(user=None):
	user = user or frappe.session.user
	return bool(set(frappe.get_roles(user)).intersection(INTERNAL_ROLES))


def _get_request_customer(requested_customer=None):
	_require_portal_user()

	customer = get_customer_for_user(frappe.session.user)
	if customer:
		return customer

	if _is_internal_user():
		customer = requested_customer or frappe.form_dict.get("customer")
		if customer:
			return customer

	frappe.throw("No customer account is linked to this user.", frappe.PermissionError)


def _customer_display(customer):
	return frappe.db.get_value("Customer", customer, "customer_name") or customer


def _customer_profile(customer, user_email=None):
	fields = ["name", "customer_name", "customer_group", "territory", "tax_id"]
	customer_doc = frappe.db.get_value("Customer", customer, fields, as_dict=True) or frappe._dict()
	contact = None
	if user_email:
		contact_name = frappe.db.get_value("Contact Email", {"email_id": user_email}, "parent")
		if contact_name and frappe.db.exists(
			"Dynamic Link",
			{"parent": contact_name, "parenttype": "Contact", "link_doctype": "Customer", "link_name": customer},
		):
			contact = frappe.get_doc("Contact", contact_name)

	address = None
	address_link = frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Address", "link_doctype": "Customer", "link_name": customer},
		pluck="parent",
		order_by="idx asc",
		limit=1,
	)
	if address_link:
		address_doc = frappe.get_doc("Address", address_link[0])
		address = {
			"line1": address_doc.address_line1,
			"line2": address_doc.address_line2,
			"city": address_doc.city,
			"state": address_doc.state,
			"country": address_doc.country,
			"postal_code": address_doc.pincode,
		}

	return {
		"name": customer_doc.name or customer,
		"display_name": customer_doc.customer_name or customer,
		"customer_group": customer_doc.customer_group,
		"territory": customer_doc.territory,
		"tax_id": customer_doc.tax_id,
		"contact_email": next((row.email_id for row in contact.email_ids if row.is_primary), None) if contact else None,
		"contact_phone": next((row.phone for row in contact.phone_nos if row.is_primary_phone), None) if contact else None,
		"address": address,
	}


def _get_vehicle_customer(vehicle):
	return frappe.db.get_value("Fleet Vehicle", vehicle, "customer")


def _validate_vehicle_access(vehicle, customer):
	vehicle_customer = _get_vehicle_customer(vehicle)
	if not vehicle_customer:
		frappe.throw("Vehicle was not found.", frappe.DoesNotExistError)
	if vehicle_customer != customer:
		frappe.throw("You do not have access to this vehicle.", frappe.PermissionError)


def _validate_ticket_access(ticket, customer):
	ticket_customer = frappe.db.get_value("Issue", ticket, "customer")
	if not ticket_customer:
		frappe.throw("Support ticket was not found.", frappe.DoesNotExistError)
	if ticket_customer != customer:
		frappe.throw("You do not have access to this support ticket.", frappe.PermissionError)


def _doctype_has_field(doctype, fieldname):
	return frappe.get_meta(doctype).has_field(fieldname)


def _legal_status(customer, user=None):
	user = user or frappe.session.user
	accepted = frappe.db.exists(
		"Omni Legal Acceptance",
		{
			"customer": customer,
			"user": user,
			"accepted_terms": 1,
			"terms_version": CURRENT_TERMS_VERSION,
			"accepted_privacy_policy": 1,
			"privacy_policy_version": CURRENT_PRIVACY_POLICY_VERSION,
		},
	)
	return {
		"accepted": bool(accepted),
		"terms_version": CURRENT_TERMS_VERSION,
		"privacy_policy_version": CURRENT_PRIVACY_POLICY_VERSION,
		"terms_url": TERMS_URL,
		"privacy_policy_url": PRIVACY_POLICY_URL,
		"accepted_record": accepted,
	}


def _require_legal_acceptance(customer):
	if _is_internal_user():
		return
	status = _legal_status(customer)
	if not status["accepted"]:
		frappe.throw("Please accept the current Terms and Privacy Policy before using the customer portal.", frappe.PermissionError)


def _request_ip():
	request = getattr(frappe.local, "request", None)
	if not request:
		return None
	for header in ("X-Forwarded-For", "X-Real-IP"):
		value = request.headers.get(header)
		if value:
			return value.split(",")[0].strip()
	return request.remote_addr


def _request_user_agent():
	request = getattr(frappe.local, "request", None)
	if not request:
		return None
	return request.headers.get("User-Agent")


def _first_unit_link_by_vehicle(customer):
	links = frappe.get_all(
		"Telematics Unit Link",
		filters={"customer": customer},
		fields=[
			"name",
			"vehicle",
			"provider",
			"status",
			"external_unit_name",
			"sync_enabled",
			"last_position_datetime",
			"latitude",
			"longitude",
			"speed",
			"ignition",
			"odometer",
			"last_sync_datetime",
			"last_sync_status",
		],
		order_by="last_position_datetime desc, modified desc",
	)
	by_vehicle = {}
	for link in links:
		if link.vehicle and link.vehicle not in by_vehicle:
			by_vehicle[link.vehicle] = link
	return by_vehicle


def _format_latest_telematics(link):
	if not link:
		return None
	return {
		"link": link.name,
		"provider": link.provider,
		"status": link.status,
		"sync_enabled": bool(link.sync_enabled),
		"unit_name": link.external_unit_name,
		"last_seen": link.last_position_datetime,
		"last_sync": link.last_sync_datetime,
		"last_sync_status": link.last_sync_status,
		"latitude": link.latitude,
		"longitude": link.longitude,
		"speed": link.speed,
		"ignition": bool(link.ignition),
		"odometer": link.odometer,
	}


def _sanitize_vehicle_detail_for_portal(data):
	telematics = data.get("telematics") or {}
	safe_links = []
	for link in telematics.get("links") or []:
		safe_links.append(
			{
				"name": link.get("name"),
				"provider": link.get("provider"),
				"status": link.get("status"),
				"external_unit_name": link.get("external_unit_name"),
				"last_sync_datetime": link.get("last_sync_datetime"),
				"last_sync_status": link.get("last_sync_status"),
				"sync_enabled": bool(link.get("sync_enabled")),
			}
		)
	telematics["links"] = safe_links
	data["telematics"] = telematics
	if data.get("tracker"):
		data["tracker"].pop("imei", None)
	if data.get("sim"):
		data["sim"].pop("msisdn", None)
	return data


@frappe.whitelist()
def get_current_customer(customer=None):
	customer = _get_request_customer(customer)
	user = frappe.get_doc("User", frappe.session.user)
	roles = frappe.get_roles(frappe.session.user)
	legal_status = _legal_status(customer)
	if _is_internal_user():
		legal_status["accepted"] = True

	return {
		"user": {
			"email": user.email,
			"full_name": user.full_name,
		},
		"customer": _customer_profile(customer, user.email),
		"roles": [role for role in roles if role in {PORTAL_ROLE, *INTERNAL_ROLES}],
		"legal": legal_status,
	}


@frappe.whitelist()
def accept_legal_terms(customer=None, accepted_terms=0, accepted_privacy_policy=0):
	customer = _get_request_customer(customer)
	if _is_internal_user():
		frappe.throw("Internal users do not need to accept customer portal terms.", frappe.PermissionError)

	if not int(accepted_terms or 0) or not int(accepted_privacy_policy or 0):
		frappe.throw("You must accept both the Terms and Privacy Policy to continue.")

	status = _legal_status(customer)
	if status["accepted"]:
		return status

	doc = frappe.get_doc(
		{
			"doctype": "Omni Legal Acceptance",
			"customer": customer,
			"user": frappe.session.user,
			"accepted_on": frappe.utils.now_datetime(),
			"accepted_terms": 1,
			"terms_version": CURRENT_TERMS_VERSION,
			"terms_url": TERMS_URL,
			"accepted_privacy_policy": 1,
			"privacy_policy_version": CURRENT_PRIVACY_POLICY_VERSION,
			"privacy_policy_url": PRIVACY_POLICY_URL,
			"ip_address": _request_ip(),
			"user_agent": _request_user_agent(),
			"source": "Customer Portal",
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return _legal_status(customer)


@frappe.whitelist()
def get_dashboard_summary(customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)
	data = get_customer_fleet_360(customer)

	return {
		"customer": {
			"name": customer,
			"display_name": _customer_display(customer),
		},
		"vehicles": {
			"total": data["summary"].get("vehicle_count") or 0,
			"online": data["summary"].get("live_telematics_count") or 0,
			"offline": max(
				(data["summary"].get("tracker_count") or 0) - (data["summary"].get("live_telematics_count") or 0),
				0,
			),
		},
		"invoices": {
			"outstanding_total": data["profile"].get("invoice_outstanding_amount") or 0,
			"open_count": data["summary"].get("open_invoice_count") or 0,
		},
		"support": {
			"open_tickets": data["summary"].get("open_ticket_count") or 0,
		},
		"documents": {
			"total": data["summary"].get("portal_document_count") or 0,
			"expiring_soon": data["summary"].get("expiring_document_count") or 0,
		},
		"maintenance": {
			"open": data["summary"].get("open_maintenance_count") or 0,
		},
	}


@frappe.whitelist()
def get_vehicles(customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)
	links_by_vehicle = _first_unit_link_by_vehicle(customer)
	vehicles = frappe.get_all(
		"Fleet Vehicle",
		filters={"customer": customer},
		fields=[
			"name",
			"registration_number",
			"vehicle_name",
			"vehicle_type",
			"status",
			"make",
			"model",
			"year",
			"odometer",
		],
		order_by="registration_number asc, modified desc",
	)

	return {
		"vehicles": [
			{
				"name": vehicle.name,
				"registration_number": vehicle.registration_number,
				"display_name": vehicle.vehicle_name or vehicle.registration_number or vehicle.name,
				"vehicle_type": vehicle.vehicle_type,
				"status": vehicle.status,
				"make": vehicle.make,
				"model": vehicle.model,
				"year": vehicle.year,
				"odometer": vehicle.odometer,
				"latest_telematics": _format_latest_telematics(links_by_vehicle.get(vehicle.name)),
			}
			for vehicle in vehicles
		]
	}


@frappe.whitelist()
def get_vehicle_detail(vehicle, customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)
	_validate_vehicle_access(vehicle, customer)
	return _sanitize_vehicle_detail_for_portal(get_vehicle_360(vehicle))


@frappe.whitelist()
def get_invoices(customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)
	fields = ["name", "posting_date", "due_date", "status", "grand_total", "outstanding_amount"]
	if _doctype_has_field("Sales Invoice", "fiscalisation_status"):
		fields.append("fiscalisation_status")

	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1},
		fields=fields,
		order_by="posting_date desc, creation desc",
		limit=100,
	)

	return {"invoices": invoices}


@frappe.whitelist()
def get_documents(customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)
	documents = frappe.get_all(
		"Fleet Document",
		filters={"customer": customer, "portal_visible": 1, "status": ["!=", "Archived"]},
		fields=[
			"name",
			"title",
			"document_type",
			"status",
			"vehicle",
			"issue_date",
			"expiry_date",
			"reference_number",
			"attachment",
		],
		order_by="expiry_date asc, modified desc",
		limit=100,
	)

	return {
		"documents": [
			{
				"name": document.name,
				"title": document.title,
				"document_type": document.document_type,
				"status": document.status,
				"vehicle": document.vehicle,
				"issue_date": document.issue_date,
				"expires_on": document.expiry_date,
				"reference_number": document.reference_number,
				"file_url": document.attachment,
			}
			for document in documents
		]
	}


@frappe.whitelist()
def get_support_tickets(customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)
	tickets = frappe.get_all(
		"Issue",
		filters={"customer": customer},
		fields=["name", "subject", "status", "priority", "creation", "modified"],
		order_by="modified desc",
		limit=100,
	)

	return {
		"tickets": [
			{
				"name": ticket.name,
				"subject": ticket.subject,
				"status": ticket.status,
				"priority": ticket.priority,
				"created_on": ticket.creation,
				"modified": ticket.modified,
			}
			for ticket in tickets
		]
	}


@frappe.whitelist()
def get_support_ticket_detail(ticket, customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)
	_validate_ticket_access(ticket, customer)
	fields = [
		"name",
		"subject",
		"status",
		"priority",
		"description",
		"resolution_details",
		"customer",
		"raised_by",
		"opening_date",
		"creation",
		"modified",
	]
	if _doctype_has_field("Issue", "content"):
		fields.append("content")
	doc = frappe.db.get_value("Issue", ticket, fields, as_dict=True)
	return {
		"name": doc.name,
		"subject": doc.subject,
		"status": doc.status,
		"priority": doc.priority,
		"description": doc.description,
		"resolution_details": doc.resolution_details,
		"customer": doc.customer,
		"raised_by": doc.raised_by,
		"opening_date": doc.opening_date,
		"created_on": doc.creation,
		"modified": doc.modified,
		"content": doc.get("content"),
	}


@frappe.whitelist()
def create_support_ticket(subject, description=None, priority="Medium", customer=None):
	customer = _get_request_customer(customer)
	_require_legal_acceptance(customer)

	subject = (subject or "").strip()
	if not subject:
		frappe.throw("Support request subject is required.")

	if priority not in {"Low", "Medium", "High", "Urgent"}:
		priority = "Medium"

	ticket = frappe.get_doc(
		{
			"doctype": "Issue",
			"subject": subject,
			"description": (description or "").strip(),
			"customer": customer,
			"raised_by": frappe.session.user,
			"priority": priority,
			"status": "Open",
		}
	)
	ticket.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"name": ticket.name, "status": ticket.status}
