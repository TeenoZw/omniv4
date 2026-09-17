import csv
from pathlib import Path

import frappe


REQUIRED_DOCTYPES = [
	"Omni Onboarding Job",
	"Omni Onboarding Checklist Item",
	"Fleet Vehicle",
	"Fleet Driver",
	"Tracker Profile",
	"SIM Profile",
	"Tracker SIM Assignment",
	"Tracker Installation",
	"Vehicle Assignment",
	"Customer Fleet Profile",
	"Fleet Maintenance Work Order",
	"Fleet Document",
	"Fleet Contract",
	"Telematics Provider Account",
	"Telematics Discovered Account",
	"Telematics Discovered User",
	"Telematics Unit Link",
	"Telematics Sync Log",
	"Fiscal Provider Account",
	"Fiscal Device",
	"Fiscal Day",
	"Fiscal Document",
	"Fiscal Sync Log",
]

REQUIRED_ROLES = [
	"Omni Operations Admin",
	"Installation Coordinator",
	"Technician",
	"Fleet Manager",
	"Customer Portal User",
]

REQUIRED_TEMPLATE_HEADERS = {
	"01_customers_from_hubs.csv": ["legacy_hub_id", "customer_name", "customer_code"],
	"02_customer_fleet_profiles_from_hubs.csv": ["legacy_hub_id", "customer", "company"],
	"03_tracker_profiles_from_hardware.csv": ["legacy_hardware_id", "imei", "item_code"],
	"04_sim_profiles_from_sim_inventory.csv": ["legacy_sim_id", "iccid", "carrier"],
	"05_fleet_vehicles_from_vehicles.csv": ["legacy_vehicle_id", "legacy_hub_id", "registration_number"],
	"06_tracker_installations_from_assignments.csv": ["legacy_assignment_id", "legacy_hardware_id", "tracker_imei"],
	"07_sales_pipeline_from_enquiries.csv": ["legacy_enquiry_id", "status", "email"],
	"08_billing_subscriptions.csv": ["legacy_subscription_id", "legacy_hub_id", "item_code"],
}


@frappe.whitelist()
def run_smoke_checks():
	results = {
		"missing_doctypes": [doctype for doctype in REQUIRED_DOCTYPES if not frappe.db.exists("DocType", doctype)],
		"missing_roles": [role for role in REQUIRED_ROLES if not frappe.db.exists("Role", role)],
		"template_check_skipped": False,
		"missing_templates": [],
		"bad_templates": [],
		"sample_records": {},
	}

	bench_root = Path(frappe.get_app_path("omni_operations")).parents[2]
	candidates = [
		bench_root.parents[1] / "docs" / "migration_templates",
		bench_root.parents[2] / "docs" / "migration_templates",
		Path.cwd() / "docs" / "migration_templates",
	]
	template_dir = next((path for path in candidates if path.exists()), None)

	if not template_dir:
		results["template_check_skipped"] = True

	if template_dir:
		for filename, required_headers in REQUIRED_TEMPLATE_HEADERS.items():
			template_path = template_dir / filename
			if not template_path.exists():
				results["missing_templates"].append(filename)
				continue

			with template_path.open(newline="") as handle:
				headers = next(csv.reader(handle), [])

			missing_headers = [header for header in required_headers if header not in headers]
			if missing_headers:
				results["bad_templates"].append({"file": filename, "missing_headers": missing_headers})

	for doctype in REQUIRED_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			results["sample_records"][doctype] = frappe.db.count(doctype)

	results["ok"] = not any(
		[
			results["missing_doctypes"],
			results["missing_roles"],
			results["missing_templates"],
			results["bad_templates"],
		]
	)
	return results


@frappe.whitelist()
def run_security_smoke_checks(portal_user="portal-test@omni.local", allowed_customer="Mapanje Hub"):
	results = {
		"portal_user": portal_user,
		"allowed_customer": allowed_customer,
		"skipped": False,
		"home_page": None,
		"customer_profile_condition": None,
		"visible_customers": [],
		"blocked_customer": None,
		"allowed_customer_has_permission": None,
		"blocked_customer_has_permission": None,
		"visible_documents": [],
		"blocked_document_has_permission": None,
		"visible_contracts": [],
		"blocked_contract_has_permission": None,
		"support_ticket_created": None,
		"ok": False,
	}

	if not frappe.db.exists("User", portal_user):
		from omni_operations.customer_portal.provisioning import ensure_internal_portal_test_user

		ensure_internal_portal_test_user(customer=allowed_customer, email=portal_user)
		results["provisioned_portal_user"] = True
	else:
		results["provisioned_portal_user"] = False

	from omni_operations.customer_portal.api import create_support_ticket
	from omni_operations.omni_security.access import customer_fleet_profile_query, role_home_page

	previous_user = frappe.session.user
	try:
		frappe.set_user(portal_user)
		results["home_page"] = role_home_page(portal_user)
		results["customer_profile_condition"] = customer_fleet_profile_query(portal_user)
		results["visible_customers"] = [
			row.customer
			for row in frappe.get_list("Customer Fleet Profile", fields=["customer"], order_by="customer asc")
		]
		blocked_customer = frappe.db.get_value(
			"Customer Fleet Profile",
			{"customer": ["!=", allowed_customer]},
			"customer",
		)
		results["blocked_customer"] = blocked_customer

		allowed_doc = frappe.get_doc("Customer Fleet Profile", allowed_customer)
		results["allowed_customer_has_permission"] = allowed_doc.has_permission("read")
		if blocked_customer:
			blocked_doc = frappe.get_doc("Customer Fleet Profile", blocked_customer)
			results["blocked_customer_has_permission"] = blocked_doc.has_permission("read")

		results["visible_documents"] = [
			row.customer
			for row in frappe.get_list("Fleet Document", fields=["customer"], order_by="customer asc")
		]
		blocked_document = frappe.db.get_value(
			"Fleet Document",
			{"customer": ["!=", allowed_customer]},
			"name",
		)
		if blocked_document:
			results["blocked_document_has_permission"] = frappe.get_doc(
				"Fleet Document", blocked_document
			).has_permission("read")

		results["visible_contracts"] = [
			row.customer
			for row in frappe.get_list("Fleet Contract", fields=["customer"], order_by="customer asc")
		]
		blocked_contract = frappe.db.get_value(
			"Fleet Contract",
			{"customer": ["!=", allowed_customer]},
			"name",
		)
		if blocked_contract:
			results["blocked_contract_has_permission"] = frappe.get_doc(
				"Fleet Contract", blocked_contract
			).has_permission("read")

		ticket = create_support_ticket(
			"Portal security smoke check",
			"Created by the Omni security smoke check and closed immediately.",
			"Low",
		)
		results["support_ticket_created"] = ticket["name"]
		frappe.db.set_value("Issue", ticket["name"], "status", "Closed")
		frappe.db.commit()
	finally:
		frappe.set_user(previous_user)

	if results["provisioned_portal_user"] or portal_user.endswith("@omni.local"):
		_cleanup_security_smoke_artifacts(
			portal_user=portal_user,
			allowed_customer=allowed_customer,
			issue_name=results["support_ticket_created"],
		)

	results["ok"] = all(
		[
			results["home_page"] == "/portal",
			results["visible_customers"] == [allowed_customer],
			all(customer == allowed_customer for customer in results["visible_documents"]),
			all(customer == allowed_customer for customer in results["visible_contracts"]),
			results["allowed_customer_has_permission"] is True,
			results["blocked_customer_has_permission"] in {False, None},
			results["blocked_document_has_permission"] in {False, None},
			results["blocked_contract_has_permission"] in {False, None},
			bool(results["support_ticket_created"]),
		]
	)
	return results


@frappe.whitelist()
def run_portal_api_smoke_checks(portal_user="portal-test@omni.local", allowed_customer="Mapanje Hub"):
	results = {
		"portal_user": portal_user,
		"allowed_customer": allowed_customer,
		"provisioned_portal_user": False,
		"legal_acceptance_ready": False,
		"current_customer": None,
		"dashboard_vehicle_total": None,
		"vehicle_count": None,
		"vehicle_detail_checked": None,
		"invoice_count": None,
		"document_count": None,
		"ticket_count": None,
		"blocked_vehicle": None,
		"blocked_vehicle_denied": None,
		"ok": False,
	}

	if not frappe.db.exists("User", portal_user):
		from omni_operations.customer_portal.provisioning import ensure_internal_portal_test_user

		ensure_internal_portal_test_user(customer=allowed_customer, email=portal_user)
		results["provisioned_portal_user"] = True

	from omni_operations.customer_portal.api import (
		accept_legal_terms,
		get_current_customer,
		get_dashboard_summary,
		get_documents,
		get_invoices,
		get_support_tickets,
		get_vehicle_detail,
		get_vehicles,
	)

	previous_user = frappe.session.user
	try:
		frappe.set_user(portal_user)
		current_customer = get_current_customer()
		accept_legal_terms(
			customer=current_customer["customer"]["name"],
			accepted_terms=1,
			accepted_privacy_policy=1,
		)
		results["legal_acceptance_ready"] = True
		dashboard = get_dashboard_summary()
		vehicles = get_vehicles()["vehicles"]
		invoices = get_invoices()["invoices"]
		documents = get_documents()["documents"]
		tickets = get_support_tickets()["tickets"]

		results["current_customer"] = current_customer["customer"]["name"]
		results["dashboard_vehicle_total"] = dashboard["vehicles"]["total"]
		results["vehicle_count"] = len(vehicles)
		results["invoice_count"] = len(invoices)
		results["document_count"] = len(documents)
		results["ticket_count"] = len(tickets)

		if vehicles:
			detail = get_vehicle_detail(vehicles[0]["name"])
			results["vehicle_detail_checked"] = detail["vehicle"]["name"]

		blocked_vehicle = frappe.db.get_value(
			"Fleet Vehicle",
			{"customer": ["!=", allowed_customer]},
			"name",
		)
		results["blocked_vehicle"] = blocked_vehicle
		if blocked_vehicle:
			try:
				get_vehicle_detail(blocked_vehicle)
				results["blocked_vehicle_denied"] = False
			except frappe.PermissionError:
				results["blocked_vehicle_denied"] = True
	finally:
		frappe.set_user(previous_user)

	if results["provisioned_portal_user"]:
		_cleanup_security_smoke_artifacts(
			portal_user=portal_user,
			allowed_customer=allowed_customer,
		)

	results["ok"] = all(
		[
			results["legal_acceptance_ready"],
			results["current_customer"] == allowed_customer,
			results["dashboard_vehicle_total"] == results["vehicle_count"],
			results["vehicle_count"] is not None,
			results["invoice_count"] is not None,
			results["document_count"] is not None,
			results["ticket_count"] is not None,
			results["blocked_vehicle_denied"] in {True, None},
		]
	)
	return results


@frappe.whitelist()
def run_onboarding_job_smoke_checks():
	test_customer = "Mapanje Hub"
	test_email = "portal-test@omni.local"
	lead_email = f"portal-lead-test-{frappe.generate_hash(length=8).lower()}@omni.local"
	results = {
		"doctype_exists": frappe.db.exists("DocType", "Omni Onboarding Job"),
		"child_doctype_exists": frappe.db.exists("DocType", "Omni Onboarding Checklist Item"),
		"created_job": None,
		"default_checklist_count": 0,
		"progress_after_linked_lead": None,
		"guided_customer": None,
		"guided_company": None,
		"guided_profile": None,
		"guided_vehicle": None,
		"guided_portal_user": None,
		"duplicate_customer_count": None,
		"duplicate_portal_user_count": None,
		"status_indicator_ready": False,
		"ok": False,
	}

	if not results["doctype_exists"] or not results["child_doctype_exists"]:
		return results

	job = frappe.new_doc("Omni Onboarding Job")
	job.prospect_name = "Mapanje"
	job.contact_name = "Smoke Test"
	job.contact_email = test_email
	job.contact_phone = "+263000000000"
	job.source = "Internal"
	job.status = "Qualification"
	job.onboarding_owner = "Administrator"
	job.insert(ignore_permissions=True)
	results["created_job"] = job.name
	results["default_checklist_count"] = len(job.checklist)

	lead = frappe.new_doc("Lead")
	lead.first_name = "Smoke"
	lead.last_name = "Onboarding"
	lead.lead_name = "Smoke Onboarding"
	lead.company_name = test_customer
	lead.email_id = lead_email
	lead.insert(ignore_permissions=True)

	job.lead = lead.name
	job.save(ignore_permissions=True)
	results["progress_after_linked_lead"] = job.progress_percent
	results["status_indicator_ready"] = job.status == "Qualification"

	from omni_operations.onboarding.doctype.omni_onboarding_job.omni_onboarding_job import (
		create_vehicle_for_onboarding,
		ensure_customer_hub,
		ensure_fleet_profile,
		provision_portal_user,
	)

	customer_result = ensure_customer_hub(job.name)
	results["guided_customer"] = customer_result.get("customer")
	results["guided_company"] = customer_result.get("company")

	profile_result = ensure_fleet_profile(job.name)
	results["guided_profile"] = profile_result.get("customer_fleet_profile")

	vehicle_registration = f"SMOKE-{frappe.generate_hash(length=8).upper()}"
	vehicle_result = create_vehicle_for_onboarding(
		job.name,
		vehicle_registration,
		vehicle_name="Smoke Test Vehicle",
		vehicle_type="Car",
	)
	results["guided_vehicle"] = vehicle_result.get("vehicle")

	portal_result = provision_portal_user(job.name)
	results["guided_portal_user"] = portal_result.get("user")

	ensure_customer_hub(job.name)
	provision_portal_user(job.name)
	results["duplicate_customer_count"] = frappe.db.count("Customer", {"name": results["guided_customer"]})
	results["duplicate_portal_user_count"] = frappe.db.count("Portal User", {"user": results["guided_portal_user"]})

	frappe.delete_doc("Omni Onboarding Job", job.name, ignore_permissions=True, force=True)
	if results["guided_vehicle"] and frappe.db.exists("Fleet Vehicle", results["guided_vehicle"]):
		frappe.delete_doc("Fleet Vehicle", results["guided_vehicle"], ignore_permissions=True, force=True)
	frappe.delete_doc("Lead", lead.name, ignore_permissions=True, force=True)
	_cleanup_security_smoke_artifacts(
		portal_user=test_email,
		allowed_customer=test_customer,
	)
	frappe.db.commit()

	results["ok"] = all(
		[
			results["default_checklist_count"] >= 7,
			results["progress_after_linked_lead"] and results["progress_after_linked_lead"] > 0,
			results["guided_customer"],
			results["guided_company"],
			results["guided_profile"],
			results["guided_vehicle"],
			results["guided_portal_user"],
			results["duplicate_customer_count"] == 1,
			results["duplicate_portal_user_count"] == 1,
			results["status_indicator_ready"],
		]
	)
	return results


@frappe.whitelist()
def run_tracker_sim_assignment_smoke_checks():
	results = {
		"assignment_count": 0,
		"duplicate_active_sims": [],
		"duplicate_active_tracker_slots": [],
		"installed_without_customer_or_vehicle": [],
		"sim_summary_mismatches": [],
		"behavior": {},
		"ok": False,
	}

	if not frappe.db.exists("DocType", "Tracker SIM Assignment"):
		results["missing_doctype"] = True
		return results

	active_statuses = ("Prepared", "Reserved", "Assigned", "Installed")
	results["assignment_count"] = frappe.db.count("Tracker SIM Assignment")
	results["duplicate_active_sims"] = frappe.db.sql(
		"""
		select sim, count(*) as count
		from `tabTracker SIM Assignment`
		where status in %(active_statuses)s
		group by sim
		having count(*) > 1
		""",
		{"active_statuses": active_statuses},
		as_dict=True,
	)
	results["duplicate_active_tracker_slots"] = frappe.db.sql(
		"""
		select tracker, slot, count(*) as count
		from `tabTracker SIM Assignment`
		where status in %(active_statuses)s
		group by tracker, slot
		having count(*) > 1
		""",
		{"active_statuses": active_statuses},
		as_dict=True,
	)
	results["installed_without_customer_or_vehicle"] = frappe.db.sql_list(
		"""
		select name
		from `tabTracker SIM Assignment`
		where status = 'Installed'
		and (ifnull(customer, '') = '' or ifnull(vehicle, '') = '')
		"""
	)

	for assignment in frappe.get_all(
		"Tracker SIM Assignment",
		filters={"status": ["in", list(active_statuses)]},
		fields=["name", "status", "tracker", "sim", "customer", "vehicle"],
		limit=1000,
	):
		sim = frappe.db.get_value(
			"SIM Profile",
			assignment.sim,
			["current_tracker", "current_customer", "current_vehicle"],
			as_dict=True,
		)
		if not sim:
			continue
		if sim.current_tracker != assignment.tracker:
			results["sim_summary_mismatches"].append(assignment.name)
			continue
		if assignment.status in {"Assigned", "Installed"} and (
			sim.current_customer != assignment.customer or sim.current_vehicle != assignment.vehicle
		):
			results["sim_summary_mismatches"].append(assignment.name)

	results["behavior"] = _run_tracker_sim_assignment_behavior_check()
	results["ok"] = not any(
		[
			results["duplicate_active_sims"],
			results["duplicate_active_tracker_slots"],
			results["installed_without_customer_or_vehicle"],
			results["sim_summary_mismatches"],
			not results["behavior"].get("ok"),
		]
	)
	return results


def _run_tracker_sim_assignment_behavior_check():
	result = {
		"primary_prepared_allowed": False,
		"secondary_prepared_allowed": False,
		"duplicate_tracker_slot_blocked": False,
		"duplicate_active_sim_blocked": False,
		"ok": False,
	}
	tracker = "OMNI-SMOKE-TRACKER"
	second_tracker = "OMNI-SMOKE-TRACKER-2"
	sim_primary = "OMNI-SMOKE-SIM-1"
	sim_secondary = "OMNI-SMOKE-SIM-2"
	sim_duplicate = "OMNI-SMOKE-SIM-3"
	created_docs = []

	try:
		for name in [tracker, second_tracker]:
			if not frappe.db.exists("Tracker Profile", name):
				frappe.get_doc(
					{
						"doctype": "Tracker Profile",
						"imei": name,
						"tracker_name": name,
						"item_code": "TRACKER-HW-4G",
						"status": "Available",
					}
				).insert(ignore_permissions=True)
				created_docs.append(("Tracker Profile", name))

		for name in [sim_primary, sim_secondary, sim_duplicate]:
			if not frappe.db.exists("SIM Profile", name):
				frappe.get_doc(
					{
						"doctype": "SIM Profile",
						"iccid": name,
						"msisdn": name,
						"item_code": "SIM-IOT",
						"status": "Available",
					}
				).insert(ignore_permissions=True)
				created_docs.append(("SIM Profile", name))

		primary = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"status": "Prepared",
				"slot": "Primary",
				"tracker": tracker,
				"sim": sim_primary,
			}
		).insert(ignore_permissions=True)
		created_docs.append(("Tracker SIM Assignment", primary.name))
		result["primary_prepared_allowed"] = True

		secondary = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"status": "Prepared",
				"slot": "Secondary",
				"tracker": tracker,
				"sim": sim_secondary,
			}
		).insert(ignore_permissions=True)
		created_docs.append(("Tracker SIM Assignment", secondary.name))
		result["secondary_prepared_allowed"] = True

		try:
			frappe.get_doc(
				{
					"doctype": "Tracker SIM Assignment",
					"status": "Prepared",
					"slot": "Primary",
					"tracker": tracker,
					"sim": sim_duplicate,
				}
			).insert(ignore_permissions=True)
		except frappe.ValidationError:
			result["duplicate_tracker_slot_blocked"] = True

		try:
			frappe.get_doc(
				{
					"doctype": "Tracker SIM Assignment",
					"status": "Prepared",
					"slot": "Primary",
					"tracker": second_tracker,
					"sim": sim_primary,
				}
			).insert(ignore_permissions=True)
		except frappe.ValidationError:
			result["duplicate_active_sim_blocked"] = True
	finally:
		for doctype, name in reversed(created_docs):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
		frappe.db.commit()

	result["ok"] = all(
		[
			result["primary_prepared_allowed"],
			result["secondary_prepared_allowed"],
			result["duplicate_tracker_slot_blocked"],
			result["duplicate_active_sim_blocked"],
		]
	)
	return result


def _cleanup_security_smoke_artifacts(portal_user, allowed_customer, issue_name=None):
	if issue_name and frappe.db.exists("Issue", issue_name):
		frappe.delete_doc("Issue", issue_name, ignore_permissions=True, force=True)

	if frappe.db.exists("Customer", allowed_customer):
		customer_doc = frappe.get_doc("Customer", allowed_customer)
		customer_doc.portal_users = [
			row for row in customer_doc.portal_users if row.user != portal_user
		]
		customer_doc.save(ignore_permissions=True)

	for acceptance in frappe.get_all(
		"Omni Legal Acceptance",
		filters={"user": portal_user},
		pluck="name",
	):
		frappe.delete_doc("Omni Legal Acceptance", acceptance, ignore_permissions=True, force=True)

	for contact in frappe.get_all(
		"Contact Email",
		filters={"email_id": portal_user},
		fields=["parent"],
		distinct=True,
	):
		if frappe.db.exists("Contact", contact.parent):
			frappe.delete_doc("Contact", contact.parent, ignore_permissions=True, force=True)

	frappe.db.sql("delete from `tabSessions` where user = %s", portal_user)
	if frappe.db.exists("User", portal_user):
		frappe.delete_doc("User", portal_user, ignore_permissions=True, force=True)

	frappe.db.commit()


@frappe.whitelist()
def run_desk_focus_smoke_checks(user="Administrator"):
	from omni_operations.omni_setup.work_queues import get_my_work_queues

	results = {
		"user": user,
		"default_workspace": None,
		"has_workspace_manager": None,
		"visible_public_workspaces": [],
		"work_queue_count": 0,
		"ok": False,
	}

	previous_user = frappe.session.user
	try:
		frappe.set_user(user)
		results["default_workspace"] = frappe.db.get_value("User", user, "default_workspace")
		results["has_workspace_manager"] = "Workspace Manager" in frappe.get_roles(user)
		results["visible_public_workspaces"] = frappe.get_all(
			"Workspace",
			filters={"public": 1, "is_hidden": 0},
			pluck="name",
			order_by="sequence_id asc",
		)
		results["work_queue_count"] = len(get_my_work_queues().get("queues", []))
	finally:
		frappe.set_user(previous_user)

	results["ok"] = results["default_workspace"] == "Omni Operations" and results[
		"visible_public_workspaces"
	] == ["Omni Operations"] and results["work_queue_count"] > 0
	return results
