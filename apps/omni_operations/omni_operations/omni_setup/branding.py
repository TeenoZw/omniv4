import frappe


OMNI_APP_NAME = "Omni Logistics"
OMNI_LOGO_URL = "/assets/omni_operations/omni-logo.png"


def apply_omni_branding():
	"""Apply user-facing Frappe branding through standard singleton settings."""
	_set_single_values(
		"Website Settings",
		{
			"app_name": OMNI_APP_NAME,
			"app_logo": OMNI_LOGO_URL,
			"splash_image": OMNI_LOGO_URL,
			"favicon": OMNI_LOGO_URL,
		},
	)
	_set_single_values(
		"System Settings",
		{
			"app_name": OMNI_APP_NAME,
		},
	)
	_set_single_values(
		"Navbar Settings",
		{
			"app_logo": OMNI_LOGO_URL,
		},
	)
	frappe.clear_cache()


def _set_single_values(doctype, values):
	meta = frappe.get_meta(doctype)
	for fieldname, value in values.items():
		if meta.has_field(fieldname):
			frappe.db.set_single_value(doctype, fieldname, value)
