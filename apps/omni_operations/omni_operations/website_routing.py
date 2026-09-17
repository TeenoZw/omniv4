import frappe
from werkzeug.exceptions import NotFound


PUBLIC_HOST = "www.omnilogistics.co.zw"
ADMIN_HOSTS = {"admin.omnilogistics.co.zw", "admin-v4.omnilogistics.co.zw"}
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

	if host == PUBLIC_HOST and path.startswith(PUBLIC_BLOCKED_PREFIXES):
		raise NotFound()
