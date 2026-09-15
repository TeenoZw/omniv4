import frappe

from omni_operations.customer_portal.api import _legal_status
from omni_operations.fleet.customer_360 import get_customer_fleet_360, get_customer_for_user


INTERNAL_ROLES = {
	"System Manager",
	"Omni Operations Admin",
	"Fleet Manager",
	"Installation Coordinator",
	"Technician",
}


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/portal"
		raise frappe.Redirect

	customer = get_customer_for_user(frappe.session.user)
	if set(frappe.get_roles(frappe.session.user)).intersection(INTERNAL_ROLES):
		customer = (
			frappe.form_dict.get("customer")
			or customer
			or frappe.db.get_value("Customer Fleet Profile", {}, "customer", order_by="modified desc")
		)
	if not customer:
		frappe.throw("No customer account is linked to this portal user.", frappe.PermissionError)

	legal = _legal_status(customer)
	is_internal = bool(set(frappe.get_roles(frappe.session.user)).intersection(INTERNAL_ROLES))

	context.no_cache = 1
	context.title = "Omni Customer Portal"
	context.customer = customer
	context.legal = legal
	context.legal_required = not is_internal and not legal.get("accepted")
	if context.legal_required:
		return context

	context.data = get_customer_fleet_360(customer)
	context.priorities = ["Low", "Medium", "High", "Urgent"]
	return context
