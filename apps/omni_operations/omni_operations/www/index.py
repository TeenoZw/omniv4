import frappe

from omni_operations.website_routing import ADMIN_HOME, ADMIN_HOSTS


def get_context(context):
	request = getattr(frappe.local, "request", None)
	host = (request.host or "").split(":", 1)[0].lower() if request else ""
	if host in ADMIN_HOSTS:
		frappe.local.flags.redirect_location = (
			ADMIN_HOME
			if frappe.session.user != "Guest"
			else f"/login?redirect-to={ADMIN_HOME}"
		)
		raise frappe.Redirect

	context.no_cache = 1
	context.title = "Omni Logistics"
	context.portal_url = "/portal"
	context.admin_url = "https://admin.omnilogistics.co.zw/app/omni-operations"
	context.enquiry_email = "sales@omnilogistics.co.zw"
	return context
