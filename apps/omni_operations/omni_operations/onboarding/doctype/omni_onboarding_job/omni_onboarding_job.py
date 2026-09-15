import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from omni_operations.omni_setup.hub_companies import (
	ensure_customer_fleet_profile,
	ensure_customer_is_business_hub,
	get_default_hub_company,
	get_or_create_business_customer_group,
	get_or_create_zimbabwe_territory,
	is_hub_name,
)


DEFAULT_CHECKLIST = [
	("Create or confirm customer/hub", "Customer"),
	("Create customer fleet profile", "Customer Fleet Profile"),
	("Capture vehicles and required tracker count", "Fleet Vehicle"),
	("Prepare or reserve tracker/SIM kit", "Tracker SIM Assignment"),
	("Schedule installation work", "Tracker Installation"),
	("Provision customer portal user", "User"),
	("Review enquiry and qualify need", "Lead"),
	("Prepare quotation or proposal", "Quotation"),
	("Prepare first invoice or billing agreement", "Sales Invoice"),
]

READINESS_FIELDS = [
	"lead_qualified",
	"quotation_ready",
	"customer_ready",
	"vehicles_ready",
	"installation_ready",
	"portal_ready",
	"billing_ready",
]


class OmniOnboardingJob(Document):
	def before_insert(self):
		if not self.checklist:
			self._set_default_checklist()

	def validate(self):
		self._validate_customer_company()
		self._sync_checklist_completion()
		self._sync_readiness_from_links()
		self._calculate_progress()
		self._set_completed_on()

	def _set_default_checklist(self):
		for task, reference_doctype in DEFAULT_CHECKLIST:
			self.append(
				"checklist",
				{
					"task": task,
					"status": "Pending",
					"required": 1,
					"reference_doctype": reference_doctype,
				},
			)

	def _validate_customer_company(self):
		if self.customer and self.company:
			customer_company = None
			if frappe.get_meta("Customer").has_field("default_company"):
				customer_company = frappe.db.get_value("Customer", self.customer, "default_company")
			if customer_company and customer_company != self.company:
				frappe.throw("The selected customer is linked to a different default company.")

		if self.primary_vehicle and self.customer:
			vehicle_customer = frappe.db.get_value("Fleet Vehicle", self.primary_vehicle, "customer")
			if vehicle_customer and vehicle_customer != self.customer:
				frappe.throw("The selected primary vehicle belongs to a different customer.")

		if self.primary_installation and self.customer:
			installation_customer = frappe.db.get_value(
				"Tracker Installation", self.primary_installation, "customer"
			)
			if installation_customer and installation_customer != self.customer:
				frappe.throw("The selected installation belongs to a different customer.")

	def _sync_checklist_completion(self):
		for row in self.checklist:
			if row.status == "Done" and not row.completed_on:
				row.completed_on = now_datetime()
			elif row.status != "Done":
				row.completed_on = None

	def _sync_readiness_from_links(self):
		if self.lead or self.opportunity:
			self.lead_qualified = self.lead_qualified or 1
		if self.quotation:
			self.quotation_ready = self.quotation_ready or 1
		if self.customer:
			self.customer_ready = self.customer_ready or 1
			if frappe.db.exists("Fleet Vehicle", {"customer": self.customer}):
				self.vehicles_ready = self.vehicles_ready or 1
		if self.primary_vehicle:
			self.vehicles_ready = self.vehicles_ready or 1
		if self.primary_installation:
			self.installation_ready = self.installation_ready or 1
		if self.portal_user:
			self.portal_ready = self.portal_ready or 1
		if self.first_invoice or self.fleet_contract:
			self.billing_ready = self.billing_ready or 1

	def _calculate_progress(self):
		total_flags = len(READINESS_FIELDS)
		ready_flags = sum(1 for fieldname in READINESS_FIELDS if self.get(fieldname))
		self.progress_percent = round((ready_flags / total_flags) * 100, 2)

		required_rows = [row for row in self.checklist if row.required]
		if required_rows:
			done_rows = [row for row in required_rows if row.status in {"Done", "Skipped"}]
			checklist_progress = round((len(done_rows) / len(required_rows)) * 100, 2)
			self.progress_percent = max(self.progress_percent or 0, checklist_progress)

	def _set_completed_on(self):
		if self.status == "Active" and not self.completed_on:
			self.completed_on = now_datetime()
		elif self.status != "Active":
			self.completed_on = None


def _get_job(job):
	if not frappe.has_permission("Omni Onboarding Job", "write"):
		frappe.throw("Not permitted to update onboarding jobs.", frappe.PermissionError)
	return frappe.get_doc("Omni Onboarding Job", job)


def _hub_name_from_job(job):
	name = (job.customer or job.prospect_name or "").strip()
	if not name:
		frappe.throw("Enter a Prospect Name before creating a customer/hub.")
	return name if is_hub_name(name) else f"{name} Hub"


def _first_name_from_contact(job):
	contact_name = (job.contact_name or job.prospect_name or "Customer User").strip()
	parts = contact_name.split(" ", 1)
	return parts[0], parts[1] if len(parts) > 1 else ""


def _set_checklist_status(job, reference_doctype, status="Done"):
	for row in job.checklist:
		if row.reference_doctype == reference_doctype:
			row.status = status


def _ensure_contact_for_customer(job, customer):
	if not job.contact_email and not job.contact_phone:
		return None

	existing_contact = None
	if job.contact_email:
		existing_contact = frappe.db.get_value("Contact Email", {"email_id": job.contact_email}, "parent")

	if existing_contact:
		contact = frappe.get_doc("Contact", existing_contact)
	else:
		first_name, last_name = _first_name_from_contact(job)
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": first_name,
				"last_name": last_name,
			}
		)
		if job.contact_email:
			contact.append("email_ids", {"email_id": job.contact_email, "is_primary": 1})
		if job.contact_phone:
			contact.append("phone_nos", {"phone": job.contact_phone, "is_primary_phone": 1})
		contact.insert(ignore_permissions=True)

	if not any(link.link_doctype == "Customer" and link.link_name == customer for link in contact.links):
		contact.append("links", {"link_doctype": "Customer", "link_name": customer})
		contact.save(ignore_permissions=True)

	return contact.name


@frappe.whitelist()
def create_onboarding_job_from_lead(lead, owner_user=None):
	if not frappe.has_permission("Omni Onboarding Job", "create"):
		frappe.throw("Not permitted to create onboarding jobs.", frappe.PermissionError)

	lead_doc = frappe.get_doc("Lead", lead)
	existing = frappe.db.get_value("Omni Onboarding Job", {"lead": lead_doc.name})
	if existing:
		return frappe.get_doc("Omni Onboarding Job", existing).as_dict()

	job = frappe.new_doc("Omni Onboarding Job")
	job.lead = lead_doc.name
	job.prospect_name = lead_doc.lead_name or lead_doc.company_name or lead_doc.name
	job.contact_name = lead_doc.lead_name
	job.contact_email = lead_doc.email_id
	job.contact_phone = lead_doc.mobile_no or lead_doc.phone
	job.source = "Website" if lead_doc.source == "Website" or not lead_doc.source else "Other"
	job.status = "Qualification"
	job.onboarding_owner = owner_user or frappe.session.user
	job.insert()
	return job.as_dict()


@frappe.whitelist()
def ensure_customer_hub(job):
	job_doc = _get_job(job)
	customer_name = _hub_name_from_job(job_doc)

	if frappe.db.exists("Customer", customer_name):
		customer = frappe.get_doc("Customer", customer_name)
	else:
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": customer_name,
				"customer_type": "Company",
				"customer_group": get_or_create_business_customer_group(),
				"territory": get_or_create_zimbabwe_territory(),
				"disabled": 0,
			}
		).insert(ignore_permissions=True)

	ensure_customer_is_business_hub(customer.name)
	company = get_default_hub_company()
	contact = _ensure_contact_for_customer(job_doc, customer.name)

	job_doc.customer = customer.name
	job_doc.company = company
	job_doc.customer_ready = 1
	job_doc.status = "Customer Setup"
	job_doc.next_action = "Create the customer fleet profile, then add the vehicles that need tracking."
	_set_checklist_status(job_doc, "Customer")
	job_doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"customer": customer.name, "company": company, "contact": contact, "job": job_doc.name}


@frappe.whitelist()
def ensure_fleet_profile(job):
	job_doc = _get_job(job)
	if not job_doc.customer:
		ensure_customer_hub(job_doc.name)
		job_doc.reload()

	company = job_doc.company or get_default_hub_company()
	profile = ensure_customer_fleet_profile(job_doc.customer, company)
	job_doc.customer_fleet_profile = profile
	job_doc.customer_ready = 1
	job_doc.status = "Vehicle Setup"
	job_doc.next_action = "Add the customer's vehicles, then prepare or reserve tracker/SIM kits."
	_set_checklist_status(job_doc, "Customer Fleet Profile")
	job_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"customer_fleet_profile": profile, "customer": job_doc.customer, "company": company, "job": job_doc.name}


@frappe.whitelist()
def create_vehicle_for_onboarding(
	job,
	registration_number,
	vehicle_name=None,
	vehicle_type="Car",
	make=None,
	model=None,
	year=None,
	vin=None,
	odometer=None,
):
	job_doc = _get_job(job)
	if not job_doc.customer:
		ensure_customer_hub(job_doc.name)
		job_doc.reload()
	if not job_doc.customer_fleet_profile:
		ensure_fleet_profile(job_doc.name)
		job_doc.reload()

	registration_number = (registration_number or "").strip()
	if not registration_number:
		frappe.throw("Registration Number is required before adding a vehicle.")

	if frappe.db.exists("Fleet Vehicle", registration_number):
		vehicle = frappe.get_doc("Fleet Vehicle", registration_number)
		if vehicle.customer and vehicle.customer != job_doc.customer:
			frappe.throw(
				f"Vehicle {registration_number} already belongs to {vehicle.customer}. "
				"Open that vehicle record before reassigning it."
			)
	else:
		vehicle = frappe.get_doc(
			{
				"doctype": "Fleet Vehicle",
				"registration_number": registration_number,
			}
		)

	vehicle.vehicle_name = vehicle_name or vehicle.vehicle_name or registration_number
	vehicle.customer = job_doc.customer
	vehicle.company = job_doc.company or get_default_hub_company()
	vehicle.vehicle_type = vehicle_type or vehicle.vehicle_type or "Car"
	vehicle.status = vehicle.status or "Active"
	vehicle.make = make or vehicle.make
	vehicle.model = model or vehicle.model
	if year:
		vehicle.year = int(year)
	vehicle.vin = vin or vehicle.vin
	if odometer:
		vehicle.odometer = float(odometer)

	if vehicle.is_new():
		vehicle.insert(ignore_permissions=True)
	else:
		vehicle.save(ignore_permissions=True)

	job_doc.primary_vehicle = job_doc.primary_vehicle or vehicle.name
	job_doc.vehicles_ready = 1
	job_doc.status = "Vehicle Setup"
	job_doc.next_action = "Prepare or reserve the tracker/SIM kit, then schedule installation."
	_set_checklist_status(job_doc, "Fleet Vehicle")
	job_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"vehicle": vehicle.name, "customer": job_doc.customer, "company": vehicle.company, "job": job_doc.name}


@frappe.whitelist()
def provision_portal_user(job):
	job_doc = _get_job(job)
	if not job_doc.customer:
		ensure_customer_hub(job_doc.name)
		job_doc.reload()

	if not job_doc.contact_email:
		frappe.throw("Enter Contact Email before provisioning a portal user.")

	from omni_operations.customer_portal.provisioning import create_customer_portal_user

	result = create_customer_portal_user(
		customer=job_doc.customer,
		email=job_doc.contact_email,
		full_name=job_doc.contact_name or job_doc.prospect_name,
		phone=job_doc.contact_phone,
		send_welcome_email=1,
	)

	job_doc.portal_user = result["user"]
	job_doc.portal_ready = 1
	job_doc.status = "Portal Provisioning"
	job_doc.next_action = "Ask the client to confirm portal access, then prepare billing."
	_set_checklist_status(job_doc, "User")
	job_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {**result, "job": job_doc.name}


@frappe.whitelist()
def complete_onboarding(job):
	job_doc = _get_job(job)
	missing = [
		label
		for fieldname, label in (
			("lead_qualified", "Lead qualified"),
			("customer_ready", "Customer/hub ready"),
			("vehicles_ready", "Vehicles ready"),
			("installation_ready", "Installation ready"),
			("portal_ready", "Portal user ready"),
			("billing_ready", "Billing ready"),
		)
		if not job_doc.get(fieldname)
	]
	if missing:
		frappe.throw("Complete these readiness steps first: " + ", ".join(missing))

	job_doc.status = "Active"
	job_doc.next_action = "Onboarding complete. Continue account management from the customer fleet profile."
	job_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"job": job_doc.name, "status": job_doc.status, "completed_on": job_doc.completed_on}
