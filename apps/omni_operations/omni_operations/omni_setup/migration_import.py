import csv
import json
from pathlib import Path

import frappe
from frappe.utils import get_datetime, now_datetime

from omni_operations.omni_setup.commercial import get_default_company
from omni_operations.omni_setup.hub_companies import get_company_for_hub_customer, sync_hub_companies
from omni_operations.omni_setup.items import ensure_fleet_service_items


STATUS_MAP = {
	"customer": {
		"active": "Active",
		"inactive": "Inactive",
		"suspended": "On Hold",
		"deleted": "Inactive",
	},
	"vehicle": {
		"active": "Active",
		"inactive": "Inactive",
		"maintenance": "Under Maintenance",
		"retired": "Decommissioned",
	},
	"tracker": {
		"in_stock": "Available",
		"assigned": "Assigned",
		"active": "Installed",
		"faulty": "Faulty",
		"maintenance": "Faulty",
		"retired": "Retired",
	},
	"sim": {
		"in_stock": "Available",
		"assigned": "Assigned",
		"suspended": "Suspended",
		"faulty": "Lost",
		"retired": "Retired",
	},
}


def read_rows(staging_dir, filename):
	path = Path(staging_dir) / filename
	if not path.exists():
		return []
	with path.open(newline="", encoding="utf-8-sig") as handle:
		return list(csv.DictReader(handle))


def clean(value):
	return (value or "").strip()


def truthy(value):
	return clean(value).lower() in {"1", "true", "yes", "y"}


def normalise_datetime(value):
	value = clean(value)
	if not value:
		return None
	if "+" in value:
		value = value.split("+", 1)[0]
	if value.endswith("Z"):
		value = value[:-1]
	try:
		return get_datetime(value)
	except Exception:
		return None


def normalise_date(value):
	value = clean(value)
	if not value:
		return None
	return value[:10]


def mapped_status(kind, value, fallback):
	return STATUS_MAP[kind].get(clean(value).lower(), fallback)


def append_note(existing, addition):
	existing = clean(existing)
	addition = clean(addition)
	if not addition:
		return existing
	if not existing:
		return addition
	if addition in existing:
		return existing
	return f"{existing}\n{addition}"


def ensure_customer_group(group_name):
	group_name = clean(group_name).title() or "Commercial"
	if frappe.db.exists("Customer Group", group_name):
		return group_name

	parent_group = frappe.db.get_value("Customer Group", {"is_group": 1}, "name") or "All Customer Groups"
	frappe.get_doc(
		{
			"doctype": "Customer Group",
			"customer_group_name": group_name,
			"parent_customer_group": parent_group,
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return group_name


def get_default_territory():
	return frappe.db.get_value("Territory", {"is_group": 1}, "name") or "All Territories"


def ensure_item(item_code, item_name=None, is_stock_item=1):
	item_code = clean(item_code)
	if not item_code:
		item_code = "TRACKER-HW-4G"
	if frappe.db.exists("Item", item_code):
		return item_code

	item_group = "Products" if is_stock_item else "Services"
	if not frappe.db.exists("Item Group", item_group):
		item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"

	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_name or item_code,
			"item_group": item_group,
			"stock_uom": "Nos",
			"is_stock_item": is_stock_item,
		}
	).insert(ignore_permissions=True)
	return item_code


def ensure_contact(customer, contact_name, email=None, phone=None, designation=None):
	contact_name = clean(contact_name)
	email = clean(email)
	phone = clean(phone)
	if not contact_name and not email and not phone:
		return None

	existing = None
	if email:
		existing = frappe.db.get_value("Contact Email", {"email_id": email}, "parent")
	if existing:
		contact = frappe.get_doc("Contact", existing)
	else:
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": contact_name or email or phone,
				"designation": designation,
			}
		)

	if email and not any(row.email_id == email for row in contact.email_ids):
		contact.append("email_ids", {"email_id": email, "is_primary": 1})
	if phone and not any(row.phone == phone for row in contact.phone_nos):
		contact.append("phone_nos", {"phone": phone, "is_primary_phone": 1})
	if not any(link.link_doctype == "Customer" and link.link_name == customer for link in contact.links):
		contact.append("links", {"link_doctype": "Customer", "link_name": customer})

	if contact.is_new():
		contact.insert(ignore_permissions=True)
	else:
		contact.save(ignore_permissions=True)
	return contact.name


def ensure_address(customer, row):
	address_line = clean(row.get("address_line")) or clean(row.get("location"))
	if not address_line:
		return None

	address_title = f"{customer} Billing"
	existing = frappe.db.exists("Address", {"address_title": address_title, "address_type": "Billing"})
	if existing:
		address = frappe.get_doc("Address", existing)
	else:
		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": address_title,
				"address_type": "Billing",
			}
		)

	address.address_line1 = address_line
	address.city = clean(row.get("city")) or clean(row.get("location")) or "Harare"
	address.country = clean(row.get("country")) or "Zimbabwe"
	if not any(link.link_doctype == "Customer" and link.link_name == customer for link in address.links):
		address.append("links", {"link_doctype": "Customer", "link_name": customer})

	if address.is_new():
		address.insert(ignore_permissions=True)
	else:
		address.save(ignore_permissions=True)
	return address.name


def get_existing_customer(row):
	customer_name = clean(row.get("customer_name"))
	if frappe.db.exists("Customer", customer_name):
		return customer_name
	return None


def import_customers(staging_dir):
	rows = read_rows(staging_dir, "01_customers_from_hubs.csv")
	created, updated = [], []
	for row in rows:
		customer_name = clean(row.get("customer_name"))
		if not customer_name:
			continue

		customer_group = ensure_customer_group(row.get("customer_group"))
		customer = get_existing_customer(row)
		legacy_note = f"Legacy Hub ID: {clean(row.get('legacy_hub_id'))}"
		notes = append_note(row.get("notes"), legacy_note)

		if customer:
			doc = frappe.get_doc("Customer", customer)
			updated.append(customer)
		else:
			doc = frappe.get_doc({"doctype": "Customer", "customer_name": customer_name})
			created.append(customer_name)

		doc.customer_group = customer_group
		doc.territory = get_default_territory()
		doc.customer_type = "Individual" if clean(row.get("customer_group")).lower() == "individual" else "Company"
		doc.disabled = 0 if clean(row.get("status")).lower() == "active" else 1
		doc.default_currency = clean(row.get("currency")) or doc.get("default_currency")
		doc.customer_details = notes

		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)

		add_comment_once("Customer", doc.name, legacy_note)

		ensure_contact(customer_name, row.get("primary_contact_name"), row.get("primary_contact_email"), row.get("primary_contact_phone"), "Primary Contact")
		ensure_contact(customer_name, row.get("billing_contact_name"), row.get("billing_contact_email"), row.get("billing_contact_phone"), "Billing Contact")
		ensure_address(customer_name, row)

	return {"created": created, "updated": updated}


def add_comment_once(reference_doctype, reference_name, text):
	text = clean(text)
	if not text:
		return

	existing = frappe.db.exists(
		"Comment",
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"content": ["like", f"%{text}%"],
		},
	)
	if existing:
		return

	frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"content": text,
		}
	).insert(ignore_permissions=True)


def import_customer_fleet_profiles(staging_dir, company=None):
	rows = read_rows(staging_dir, "02_customer_fleet_profiles_from_hubs.csv")
	created, updated = [], []
	for row in rows:
		customer = clean(row.get("customer"))
		if not customer or not frappe.db.exists("Customer", customer):
			continue

		name = frappe.db.exists("Customer Fleet Profile", customer)
		if name:
			doc = frappe.get_doc("Customer Fleet Profile", name)
			updated.append(name)
		else:
			doc = frappe.get_doc({"doctype": "Customer Fleet Profile", "customer": customer})
			created.append(customer)

		doc.company = get_company_for_hub_customer(customer) or company
		doc.status = mapped_status("customer", row.get("profile_status"), "Active")
		doc.total_vehicles = int(clean(row.get("expected_vehicle_count")) or 0)
		doc.active_trackers = int(clean(row.get("expected_tracker_count")) or 0)
		doc.notes = append_note(row.get("notes"), f"Legacy Hub ID: {clean(row.get('legacy_hub_id'))}")

		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)
	return {"created": created, "updated": updated}


def import_trackers(staging_dir):
	rows = read_rows(staging_dir, "03_tracker_profiles_from_hardware.csv")
	created, updated = [], []
	for row in rows:
		imei = clean(row.get("imei"))
		if not imei:
			continue

		item_code = ensure_item(row.get("item_code"), row.get("model") or row.get("hardware_type"), 1)
		if frappe.db.exists("Tracker Profile", imei):
			doc = frappe.get_doc("Tracker Profile", imei)
			updated.append(imei)
		else:
			doc = frappe.get_doc({"doctype": "Tracker Profile", "imei": imei})
			created.append(imei)

		doc.item_code = item_code
		doc.tracker_name = row.get("model") or imei
		doc.status = mapped_status("tracker", row.get("status"), "Available")
		doc.manufacturer = clean(row.get("manufacturer"))
		doc.device_model = clean(row.get("model"))
		doc.firmware_version = clean(row.get("firmware_version"))
		doc.purchase_date = normalise_date(row.get("purchase_date"))
		doc.notes = append_note(row.get("notes"), f"Legacy Hardware ID: {clean(row.get('legacy_hardware_id'))}")

		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)
	return {"created": created, "updated": updated}


def import_sims(staging_dir):
	rows = read_rows(staging_dir, "04_sim_profiles_from_sim_inventory.csv")
	created, updated = [], []
	ensure_item("SIM-IOT", "IoT SIM Card", 1)
	for row in rows:
		iccid = clean(row.get("iccid"))
		if not iccid:
			continue

		if frappe.db.exists("SIM Profile", iccid):
			doc = frappe.get_doc("SIM Profile", iccid)
			updated.append(iccid)
		else:
			doc = frappe.get_doc({"doctype": "SIM Profile", "iccid": iccid})
			created.append(iccid)

		doc.msisdn = clean(row.get("msisdn"))
		doc.item_code = ensure_item(row.get("item_code") or "SIM-IOT", "IoT SIM Card", 1)
		doc.status = mapped_status("sim", row.get("status"), "Available")
		doc.carrier = clean(row.get("carrier"))
		doc.apn = clean(row.get("apn"))
		doc.roaming_enabled = 1 if truthy(row.get("roaming_enabled")) else 0
		doc.notes = append_note(row.get("notes"), f"Legacy SIM ID: {clean(row.get('legacy_sim_id'))}")

		tracker_id = clean(row.get("current_tracker_legacy_hardware_id"))
		if tracker_id:
			imei = frappe.db.get_value("Tracker Profile", {"notes": ["like", f"%Legacy Hardware ID: {tracker_id}%"]}, "name")
			if imei:
				doc.current_tracker = imei

		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)
	return {"created": created, "updated": updated}


def import_vehicles(staging_dir, company=None):
	rows = read_rows(staging_dir, "05_fleet_vehicles_from_vehicles.csv")
	created, updated = [], []
	for row in rows:
		registration = clean(row.get("registration_number")) or clean(row.get("legacy_vehicle_id"))
		customer = clean(row.get("customer"))
		if not registration or not customer or not frappe.db.exists("Customer", customer):
			continue

		if frappe.db.exists("Fleet Vehicle", registration):
			doc = frappe.get_doc("Fleet Vehicle", registration)
			updated.append(registration)
		else:
			doc = frappe.get_doc({"doctype": "Fleet Vehicle", "registration_number": registration})
			created.append(registration)

		doc.vehicle_name = clean(row.get("asset_name")) or registration
		doc.customer = customer
		doc.company = get_company_for_hub_customer(customer) or company
		doc.vehicle_type = normalise_vehicle_type(row.get("asset_type"))
		doc.status = mapped_status("vehicle", row.get("status"), "Active")
		doc.make = clean(row.get("make"))
		doc.model = clean(row.get("model"))
		doc.year = int(clean(row.get("year")) or 0) or None
		doc.vin = clean(row.get("vin"))
		doc.notes = append_note(row.get("notes"), f"Legacy Vehicle ID: {clean(row.get('legacy_vehicle_id'))}")

		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)
	return {"created": created, "updated": updated}


def normalise_vehicle_type(value):
	value = clean(value).lower()
	if value in {"truck", "car", "bus", "van", "motorcycle", "trailer"}:
		return value.title()
	if value in {"plant", "plant equipment", "generator"}:
		return "Plant Equipment"
	return "Other"


def import_installations(staging_dir, company=None):
	rows = read_rows(staging_dir, "06_tracker_installations_from_assignments.csv")
	created, updated, skipped = [], [], []
	for row in rows:
		legacy_assignment_id = clean(row.get("legacy_assignment_id"))
		customer = clean(row.get("customer"))
		vehicle = clean(row.get("vehicle")) or clean(row.get("legacy_vehicle_id"))
		if vehicle and not frappe.db.exists("Fleet Vehicle", vehicle):
			vehicle = clean(row.get("legacy_vehicle_id"))
		tracker = clean(row.get("tracker_imei"))
		sim = clean(row.get("sim_iccid"))
		if not all([legacy_assignment_id, customer, vehicle, tracker]):
			skipped.append(legacy_assignment_id)
			continue
		if not (frappe.db.exists("Customer", customer) and frappe.db.exists("Fleet Vehicle", vehicle) and frappe.db.exists("Tracker Profile", tracker)):
			skipped.append(legacy_assignment_id)
			continue

		existing = frappe.db.sql(
			"""
			select name from `tabTracker Installation`
			where coalesce(notes, '') like %s
			limit 1
			""",
			(f"%Legacy Assignment ID: {legacy_assignment_id}%",),
		)
		if existing:
			doc = frappe.get_doc("Tracker Installation", existing[0][0])
			is_new = False
		else:
			doc = frappe.get_doc({"doctype": "Tracker Installation", "naming_series": "TI-.YYYY.-.####"})
			is_new = True

		doc.status = "Completed" if clean(row.get("status")) == "Completed" else "Scheduled"
		doc.scheduled_date = normalise_datetime(row.get("assigned_at"))
		doc.completed_date = normalise_datetime(row.get("installed_at"))
		doc.customer = customer
		doc.company = get_company_for_hub_customer(customer) or company
		doc.vehicle = vehicle
		doc.tracker = tracker
		doc.sim = sim if sim and frappe.db.exists("SIM Profile", sim) else None
		doc.installation_location = clean(row.get("installation_location"))
		doc.latitude = float(clean(row.get("installation_latitude")) or 0) or None
		doc.longitude = float(clean(row.get("installation_longitude")) or 0) or None
		doc.notes = append_note(row.get("notes"), f"Legacy Assignment ID: {legacy_assignment_id}")

		if is_new:
			doc.insert(ignore_permissions=True)
			created.append(doc.name)
		else:
			doc.save(ignore_permissions=True)
			updated.append(doc.name)

		frappe.db.set_value("Tracker Profile", tracker, {"current_customer": customer, "current_vehicle": vehicle, "status": "Installed"})
		if sim and frappe.db.exists("SIM Profile", sim):
			frappe.db.set_value("SIM Profile", sim, {"current_customer": customer, "current_vehicle": vehicle, "current_tracker": tracker, "status": "Installed"})

	return {"created": created, "updated": updated, "skipped": skipped}


def import_sales_pipeline_history(staging_dir):
	rows = read_rows(staging_dir, "07_sales_pipeline_from_enquiries.csv")
	created, updated = [], []
	for row in rows:
		email = clean(row.get("email"))
		legacy_id = clean(row.get("legacy_enquiry_id"))
		if not email and not legacy_id:
			continue

		existing = None
		if email:
			existing = frappe.db.exists("Lead", {"email_id": email})
		if existing:
			doc = frappe.get_doc("Lead", existing)
			is_new = False
		else:
			doc = frappe.get_doc({"doctype": "Lead"})
			is_new = True

		doc.first_name = clean(row.get("full_name")) or clean(row.get("company_name")) or email
		doc.company_name = clean(row.get("company_name"))
		doc.email_id = email
		doc.mobile_no = clean(row.get("phone"))
		doc.status = "Lead"
		note = build_enquiry_note(row)
		if not any(legacy_id and legacy_id in clean(existing.note) for existing in doc.notes):
			doc.append("notes", {"note": note, "added_by": frappe.session.user, "added_on": now_datetime()})

		if is_new:
			doc.insert(ignore_permissions=True)
			created.append(doc.name)
		else:
			doc.save(ignore_permissions=True)
			updated.append(doc.name)
	return {"created": created, "updated": updated}


def build_enquiry_note(row):
	parts = [
		f"Legacy Enquiry ID: {clean(row.get('legacy_enquiry_id'))}",
		f"Legacy status: {clean(row.get('status'))}",
		f"Customer type: {clean(row.get('customer_type'))}",
		f"Fleet size: {clean(row.get('fleet_size'))}",
		f"Operating area: {clean(row.get('operating_area'))}",
		f"Use case: {clean(row.get('tracking_use_case'))}",
		f"Hardware choices: {clean(row.get('hardware_choices'))}",
		f"Add-ons: {clean(row.get('add_ons'))}",
		f"Quoted monthly: {clean(row.get('quoted_monthly'))}",
		f"Quoted hardware total: {clean(row.get('quoted_hardware_total'))}",
		f"Message: {clean(row.get('message'))}",
		f"Admin notes: {clean(row.get('admin_notes'))}",
	]
	return "\n".join(part for part in parts if not part.endswith(": "))


def attach_billing_history(staging_dir):
	rows = read_rows(staging_dir, "08_billing_subscriptions.csv")
	updated, skipped = [], []
	for row in rows:
		customer = clean(row.get("customer"))
		if not customer or not frappe.db.exists("Customer Fleet Profile", customer):
			skipped.append(clean(row.get("legacy_subscription_id")))
			continue

		doc = frappe.get_doc("Customer Fleet Profile", customer)
		note = (
			f"Legacy Subscription ID: {clean(row.get('legacy_subscription_id'))}\n"
			f"Tier: {clean(row.get('tier'))}\n"
			f"Start: {clean(row.get('start_date'))}\n"
			f"End: {clean(row.get('end_date'))}\n"
			f"Active: {clean(row.get('is_active'))}\n"
			f"Auto renew: {clean(row.get('auto_renew'))}\n"
			f"Billing cycle: {clean(row.get('billing_cycle'))}\n"
			f"Payment method: {clean(row.get('payment_method'))}"
		)
		doc.contract_notes = append_note(doc.contract_notes, note)
		doc.save(ignore_permissions=True)
		updated.append(customer)
	return {"updated": sorted(set(updated)), "skipped": skipped}


def refresh_imported_customer_fleet_profiles():
	updated = []
	profiles = frappe.get_all("Customer Fleet Profile", fields=["name", "customer"])
	for profile in profiles:
		customer = profile.customer
		doc = frappe.get_doc("Customer Fleet Profile", profile.name)
		vehicles = frappe.get_all(
			"Fleet Vehicle",
			filters={"customer": customer},
			fields=["name"],
			order_by="modified desc",
		)
		trackers = frappe.get_all(
			"Tracker Profile",
			filters={"current_customer": customer, "status": ["in", ["Assigned", "Installed"]]},
			fields=["name"],
			order_by="modified desc",
		)
		sims = frappe.get_all(
			"SIM Profile",
			filters={"current_customer": customer, "status": ["in", ["Assigned", "Installed"]]},
			fields=["name"],
			order_by="modified desc",
		)
		installations = frappe.get_all(
			"Tracker Installation",
			filters={"customer": customer},
			fields=["name", "vehicle", "tracker", "sim"],
			order_by="modified desc",
			limit=1,
		)

		doc.total_vehicles = len(vehicles)
		doc.active_trackers = len(trackers)
		doc.installed_sims = len(sims)
		if vehicles:
			doc.primary_vehicle = vehicles[0].name
		if trackers:
			doc.primary_tracker = trackers[0].name
		if sims:
			doc.primary_sim = sims[0].name
		if installations:
			doc.last_installation = installations[0].name

		doc.save(ignore_permissions=True)
		updated.append(customer)
	return updated


@frappe.whitelist()
def import_from_staging(staging_dir):
	staging_dir = Path(staging_dir)
	if not staging_dir.exists():
		frappe.throw(f"Staging directory not found: {staging_dir}")

	ensure_fleet_service_items()

	report = {
		"customers": import_customers(staging_dir),
		"hub_companies": sync_hub_companies(),
		"company": get_default_company(),
		"customer_fleet_profiles": import_customer_fleet_profiles(staging_dir),
		"trackers": import_trackers(staging_dir),
		"sims": import_sims(staging_dir),
		"vehicles": import_vehicles(staging_dir),
		"installations": import_installations(staging_dir),
		"sales_pipeline_history": import_sales_pipeline_history(staging_dir),
		"billing_history": attach_billing_history(staging_dir),
	}
	report["hub_companies_after_import"] = sync_hub_companies()
	report["refreshed_customer_fleet_profiles"] = refresh_imported_customer_fleet_profiles()

	frappe.db.commit()
	report_path = staging_dir / "erpnext_import_report.json"
	report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
	return report
