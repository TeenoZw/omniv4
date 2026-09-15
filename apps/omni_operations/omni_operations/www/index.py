import frappe


def get_context(context):
	request = getattr(frappe.local, "request", None)
	host = (request.host or "").split(":", 1)[0].lower() if request else ""
	if host == "admin.omnilogistics.co.zw":
		frappe.local.flags.redirect_location = "/app/omni-operations"
		raise frappe.Redirect

	context.no_cache = 1
	context.title = "Omni Logistics"
	context.portal_url = "/portal"
	context.admin_url = "https://admin.omnilogistics.co.zw/app/omni-operations"
	context.enquiry_email = "sales@omnilogistics.co.zw"
	return context
