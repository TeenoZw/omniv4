import frappe

from omni_operations.fleet.customer_360 import get_customer_for_user


INTERNAL_ROLES = {
	"System Manager",
	"Omni Operations Admin",
	"Fleet Manager",
	"Installation Coordinator",
	"Technician",
}

PORTAL_ROLE = "Customer Portal User"

CUSTOMER_FIELD_BY_DOCTYPE = {
	"Omni Onboarding Job": "customer",
	"Customer Fleet Profile": "customer",
	"Fleet Vehicle": "customer",
	"Fleet Driver": "customer",
	"Vehicle Assignment": "customer",
	"Tracker Installation": "customer",
	"Tracker SIM Assignment": "customer",
	"Fleet Maintenance Work Order": "customer",
	"Fleet Document": "customer",
	"Fleet Contract": "customer",
	"Telematics Unit Link": "customer",
	"Fiscal Document": "customer",
	"Sales Invoice": "customer",
	"Issue": "customer",
}


def role_home_page(user):
	if user == "Guest":
		return "index"
	if is_portal_only_user(user):
		return "/portal"
	return "/app/omni-operations"


def get_customer_query_conditions_for(doctype, user=None):
	user = user or frappe.session.user
	if not should_scope_to_customer(user):
		return None

	fieldname = CUSTOMER_FIELD_BY_DOCTYPE.get(doctype)
	customer = get_customer_for_user(user)
	if not fieldname or not customer:
		return "1 = 0"

	return f"`tab{doctype}`.`{fieldname}` = {frappe.db.escape(customer)}"


def customer_fleet_profile_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Customer Fleet Profile", user)


def omni_onboarding_job_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Omni Onboarding Job", user)


def fleet_vehicle_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Fleet Vehicle", user)


def fleet_driver_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Fleet Driver", user)


def vehicle_assignment_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Vehicle Assignment", user)


def tracker_installation_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Tracker Installation", user)


def tracker_sim_assignment_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Tracker SIM Assignment", user)


def fleet_maintenance_work_order_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Fleet Maintenance Work Order", user)


def fleet_document_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Fleet Document", user)


def fleet_contract_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Fleet Contract", user)


def telematics_unit_link_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Telematics Unit Link", user)


def fiscal_document_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Fiscal Document", user)


def sales_invoice_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Sales Invoice", user)


def issue_query(user=None, doctype=None):
	return get_customer_query_conditions_for("Issue", user)


def has_customer_permission(doc, user=None, ptype=None, **kwargs):
	user = user or frappe.session.user
	if not should_scope_to_customer(user):
		return True

	customer = get_customer_for_user(user)
	if not customer:
		return False

	doc_customer = getattr(doc, CUSTOMER_FIELD_BY_DOCTYPE.get(doc.doctype, "customer"), None)
	if doc.doctype == "Customer Fleet Profile" and not doc_customer:
		doc_customer = doc.name

	return doc_customer == customer


def should_scope_to_customer(user):
	if user in {"Administrator", "Guest"}:
		return False

	roles = set(frappe.get_roles(user))
	if roles.intersection(INTERNAL_ROLES):
		return False

	return PORTAL_ROLE in roles


def is_portal_only_user(user):
	if user in {"Administrator", "Guest"}:
		return False

	roles = set(frappe.get_roles(user))
	return PORTAL_ROLE in roles and not roles.intersection(INTERNAL_ROLES)
