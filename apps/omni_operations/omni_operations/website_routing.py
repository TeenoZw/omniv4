import frappe
from werkzeug.exceptions import NotFound


PUBLIC_HOST = "www.omnilogistics.co.zw"
ADMIN_HOST = "admin.omnilogistics.co.zw"
ADMIN_HOME = "/app/omni-operations"

PUBLIC_BLOCKED_PREFIXES = (
	"/app",
	"/desk",
	"/api/method/frappe.desk",
)


def before_request():
	request = getattr(frappe.local, "request", None)
	if not request:
		return

	host = (request.host or "").split(":", 1)[0].lower()
	path = request.path or "/"

	if host == ADMIN_HOST and path == "/":
		frappe.local.flags.redirect_location = ADMIN_HOME
		raise frappe.Redirect

	if host == PUBLIC_HOST and path.startswith(PUBLIC_BLOCKED_PREFIXES):
		raise NotFound()
