import json
import re

import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, escape_html, get_datetime, now_datetime, validate_email_address


ALLOWED_CONTACT_METHODS = {"email", "phone", "whatsapp"}


def _clean(value, limit=500):
	return (value or "").strip()[:limit]


def _as_list(value):
	if isinstance(value, list):
		return value
	if not value:
		return []
	try:
		parsed = json.loads(value)
		return parsed if isinstance(parsed, list) else []
	except (TypeError, ValueError):
		return []


def _format_request(payload):
	segments = _as_list(payload.get("fleet_segments"))
	hardware = _as_list(payload.get("hardware_choices"))
	add_ons = _as_list(payload.get("add_ons"))
	lines = [
		"Website quote request",
		f"Fleet size: {cint(payload.get('fleet_size'))}",
		f"Operating area: {_clean(payload.get('operating_area')) or 'Not supplied'}",
		f"Preferred contact: {_clean(payload.get('preferred_contact_method')) or 'Email'}",
		f"Target go-live: {_clean(payload.get('expected_go_live_date')) or 'Not supplied'}",
	]
	if segments:
		lines.append("Fleet mix:")
		for segment in segments[:20]:
			lines.append(f"- {cint(segment.get('count'))} x {_clean(segment.get('label') or segment.get('vehicle_type'), 120)}")
	if hardware:
		lines.append("Hardware: " + ", ".join(_clean(item, 120) for item in hardware[:20]))
	if add_ons:
		lines.append("Add-ons: " + ", ".join(_clean(item, 120) for item in add_ons[:20]))
	if _clean(payload.get("tracking_use_case"), 4000):
		lines.extend(["", _clean(payload.get("tracking_use_case"), 4000)])
	if _clean(payload.get("message"), 2000):
		lines.extend(["", "Client message:", _clean(payload.get("message"), 2000)])
	lines.extend([
		"",
		f"Terms accepted: Yes ({now_datetime()})",
		f"Privacy Policy accepted: Yes ({now_datetime()})",
	])
	return "\n".join(lines)


def _ensure_website_lead_source():
	if not frappe.db.exists("Lead Source", "Website"):
		frappe.get_doc({"doctype": "Lead Source", "source_name": "Website"}).insert(ignore_permissions=True)
	return "Website"


@frappe.whitelist(allow_guest=True)
@rate_limit(key="email", limit=5, seconds=60 * 60)
def submit_quote_request(**payload):
	"""Create the sales and onboarding records for a public quote request."""
	# A hidden field can be added by automated clients but is never shown to people.
	if _clean(payload.get("website")):
		return {"received": True}

	full_name = _clean(payload.get("full_name"), 140)
	email = _clean(payload.get("email"), 140).lower()
	phone = _clean(payload.get("phone"), 40)
	company_name = _clean(payload.get("company_name"), 140)
	if not full_name or not email or not phone:
		frappe.throw("Full name, email address, and phone number are required.")
	if not validate_email_address(email, throw=False):
		frappe.throw("Enter a valid email address.")
	if not re.match(r"^[+\d][\d\s()\-]{7,}$", phone):
		frappe.throw("Enter a valid phone number.")
	if not cint(payload.get("terms_accepted")) or not cint(payload.get("privacy_accepted")):
		frappe.throw("Accept the Terms & Conditions and Privacy Policy before requesting a quote.")

	fleet_size = max(0, cint(payload.get("fleet_size")))
	if fleet_size < 1:
		frappe.throw("Add at least one vehicle or asset to the fleet mix.")
	preferred_contact = _clean(payload.get("preferred_contact_method"), 20).lower() or "email"
	if preferred_contact not in ALLOWED_CONTACT_METHODS:
		frappe.throw("Choose a valid preferred contact method.")
	target_date = _clean(payload.get("expected_go_live_date"), 20)
	if target_date:
		get_datetime(target_date)

	request_notes = _format_request(payload)
	lead_source = _ensure_website_lead_source()
	lead = frappe.get_doc({
		"doctype": "Lead",
		"lead_name": full_name,
		"company_name": company_name,
		"email_id": email,
		"mobile_no": phone,
		"source": lead_source,
		"notes": [{
			"note": "<br>".join(escape_html(request_notes).splitlines()),
			"added_by": "Guest",
			"added_on": now_datetime(),
		}],
	}).insert(ignore_permissions=True)

	job = frappe.get_doc({
		"doctype": "Omni Onboarding Job",
		"status": "Qualification",
		"priority": "Medium",
		"source": "Website",
		"prospect_name": company_name or full_name,
		"lead": lead.name,
		"contact_name": full_name,
		"contact_email": email,
		"contact_phone": phone,
		"estimated_vehicles": fleet_size,
		"target_go_live_date": target_date or None,
		"next_action": "Review the quote request, confirm requirements, then prepare a quotation.",
		"notes": request_notes,
	}).insert(ignore_permissions=True)

	frappe.db.commit()
	return {
		"received": True,
		"reference": job.name,
		"message": "Your quote request has been received.",
	}
