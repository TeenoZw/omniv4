from datetime import datetime
import json
import re

import frappe
from frappe.utils import get_datetime, now_datetime

from omni_operations.telematics.providers.registry import get_provider


@frappe.whitelist()
def discover_provider_hierarchy(provider_account_name):
	return {
		"accounts": discover_provider_accounts(provider_account_name),
		"users": discover_provider_users(provider_account_name),
		"units": sync_provider_units(provider_account_name),
	}


@frappe.whitelist()
def discover_provider_accounts(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	started = now_datetime()
	processed = created = updated = failed = 0
	try:
		for account in provider.list_accounts():
			processed += 1
			try:
				values = _provider_account_values(account)
				existing = frappe.db.exists(
					"Telematics Discovered Account",
					{"provider_account": provider_account.name, "external_account_id": account.external_account_id},
				)
				if existing:
					doc = frappe.get_doc("Telematics Discovered Account", existing)
					for fieldname, value in values.items():
						setattr(doc, fieldname, value)
					doc.save(ignore_permissions=True)
					updated += 1
				else:
					frappe.get_doc({
						"doctype": "Telematics Discovered Account",
						"provider_account": provider_account.name,
						"external_account_id": account.external_account_id,
						"first_discovered": now_datetime(),
						**values,
					}).insert(ignore_permissions=True)
					created += 1
			except Exception:
				failed += 1
				frappe.log_error(title=f"Telematics account discovery failed for {account.account_name}", message=frappe.get_traceback())
		status = "Success" if failed == 0 else "Warning"
		error_message = None if failed == 0 else f"{failed} provider account(s) could not be stored."
	except Exception as exc:
		status = "Failed"
		error_message = str(exc)

	log = _discovery_log(
		provider_account, "Account Discovery", status, started, processed, created, updated, failed,
		f"Discovered customer accounts from {provider_account.provider}.", error_message,
	)
	frappe.db.commit()
	return {"status": status, "sync_log": log.name, "records_processed": processed, "records_created": created,
		"records_updated": updated, "records_failed": failed, "error_message": error_message}


@frappe.whitelist()
def discover_provider_users(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	started = now_datetime()
	processed = created = updated = failed = 0

	try:
		users = provider.list_users()
		for user in users:
			processed += 1
			try:
				values = _provider_user_values(user)
				existing = frappe.db.exists(
					"Telematics Discovered User",
					{"provider_account": provider_account.name, "external_user_id": user.external_user_id},
				)
				if existing:
					doc = frappe.get_doc("Telematics Discovered User", existing)
					for fieldname, value in values.items():
						setattr(doc, fieldname, value)
					doc.save(ignore_permissions=True)
					updated += 1
				else:
					frappe.get_doc(
						{
							"doctype": "Telematics Discovered User",
							"provider_account": provider_account.name,
							"external_user_id": user.external_user_id,
							"first_discovered": now_datetime(),
							**values,
						}
					).insert(ignore_permissions=True)
					created += 1
			except Exception:
				failed += 1
				frappe.log_error(title=f"Telematics user discovery failed for {user.username}", message=frappe.get_traceback())

		status = "Success" if failed == 0 else "Warning"
		error_message = None if failed == 0 else f"{failed} provider user(s) could not be stored."
		_refresh_discovered_account_hierarchy(provider_account.name)
	except Exception as exc:
		status = "Failed"
		error_message = str(exc)

	log = frappe.get_doc(
		{
			"doctype": "Telematics Sync Log",
			"provider_account": provider_account.name,
			"sync_type": "User Discovery",
			"status": status,
			"started_datetime": started,
			"finished_datetime": now_datetime(),
			"records_processed": processed,
			"records_created": created,
			"records_updated": updated,
			"records_failed": failed,
			"request_summary": f"Discovered users and account hierarchy from {provider_account.provider}.",
			"response_summary": f"Processed {processed}; created {created}; updated {updated}; failed {failed}.",
			"error_message": error_message,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"status": status,
		"sync_log": log.name,
		"records_processed": processed,
		"records_created": created,
		"records_updated": updated,
		"records_failed": failed,
		"error_message": error_message,
	}


@frappe.whitelist()
def activate_discovered_account(discovered_account_name):
	if not frappe.has_permission("Telematics Discovered Account", "write"):
		frappe.throw("Not permitted to activate provider accounts.", frappe.PermissionError)

	account = frappe.get_doc("Telematics Discovered Account", discovered_account_name)
	if account.activation_status == "Activated" and account.customer:
		vehicle_import = link_approved_account_units(account.name, commit=False)
		frappe.db.commit()
		return {"account": account.name, "customer": account.customer, "onboarding_job": account.onboarding_job,
			"vehicle_import": vehicle_import}
	if account.activation_status == "Ignored":
		frappe.throw("Change the account from Ignored to Pending Verification before activating it.")
	if account.account_type != "Customer Hub":
		frappe.throw("Only a discovered Customer Hub can be activated as an Omni customer.")
	if account.duplicate_status in {"Possible Duplicate", "Multiple Matches"}:
		frappe.throw("Resolve the possible duplicate customer before activating this account.")

	from omni_operations.omni_setup.hub_companies import (
		ensure_customer_fleet_profile,
		get_default_hub_company,
		get_or_create_business_customer_group,
		get_or_create_zimbabwe_territory,
	)

	customer_name = account.suggested_existing_customer or account.account_name.strip()
	if frappe.db.exists("Customer", customer_name):
		customer = frappe.get_doc("Customer", customer_name)
	else:
		customer = frappe.get_doc({
			"doctype": "Customer", "customer_name": customer_name, "customer_type": "Company",
			"customer_group": get_or_create_business_customer_group(),
			"territory": get_or_create_zimbabwe_territory(), "disabled": 0,
		}).insert(ignore_permissions=True)
	company = get_default_hub_company()
	profile = ensure_customer_fleet_profile(customer.name, company)

	contact_user = frappe.db.get_value(
		"Telematics Discovered User",
		{"provider_account": account.provider_account, "account_id": account.external_account_id},
		["username", "email", "two_factor_phone"], as_dict=True,
	)
	job = frappe.get_doc({
		"doctype": "Omni Onboarding Job", "prospect_name": customer_name, "customer": customer.name,
		"company": company, "customer_fleet_profile": profile, "source": "Partner", "status": "Vehicle Setup",
		"contact_name": contact_user.username if contact_user else None,
		"contact_email": contact_user.email if contact_user else None,
		"contact_phone": contact_user.two_factor_phone if contact_user else None,
		"customer_ready": 1,
		"next_action": "Verify discovered users and units, then add or match the customer's vehicles.",
	})
	job.insert(ignore_permissions=True)
	for checklist_item in job.checklist:
		if checklist_item.reference_doctype in {"Customer", "Customer Fleet Profile"}:
			checklist_item.status = "Done"
	job.save(ignore_permissions=True)

	account.customer = customer.name
	account.onboarding_job = job.name
	account.activation_status = "Activated"
	account.verified_by = frappe.session.user
	account.verified_on = now_datetime()
	account.save(ignore_permissions=True)
	for user_name in frappe.get_all(
		"Telematics Discovered User",
		filters={"provider_account": account.provider_account, "account_id": account.external_account_id},
		pluck="name",
	):
		frappe.db.set_value(
			"Telematics Discovered User", user_name,
			{"customer": customer.name, "review_status": "Mapped to Customer"}, update_modified=False,
		)
	for unit_link_name in frappe.get_all(
		"Telematics Unit Link",
		filters={"provider_account": account.provider_account, "external_account_id": account.external_account_id, "status": "Unlinked"},
		pluck="name",
	):
		frappe.db.set_value(
			"Telematics Unit Link", unit_link_name, "suggested_customer", customer.name, update_modified=False,
		)
	vehicle_import = link_approved_account_units(account.name, commit=False)
	frappe.db.commit()
	return {"account": account.name, "customer": customer.name, "fleet_profile": profile, "onboarding_job": job.name,
		"vehicle_import": vehicle_import}


@frappe.whitelist()
def link_approved_account_units(discovered_account_name, commit=True):
	"""Link units owned by an approved provider account without moving existing ownership."""
	if not frappe.has_permission("Telematics Discovered Account", "write"):
		frappe.throw("Not permitted to link provider units.", frappe.PermissionError)

	account = frappe.get_doc("Telematics Discovered Account", discovered_account_name)
	if account.account_type != "Customer Hub" or account.activation_status != "Activated" or not account.customer:
		frappe.throw("Activate this Customer Hub before linking its vehicles.")

	company = frappe.db.get_value("Omni Onboarding Job", account.onboarding_job, "company")
	if not company:
		from omni_operations.omni_setup.hub_companies import get_default_hub_company
		company = get_default_hub_company()

	result = {"processed": 0, "created": [], "linked": [], "already_linked": [], "conflicts": []}
	unit_links = frappe.get_all(
		"Telematics Unit Link",
		filters={"provider_account": account.provider_account, "external_account_id": account.external_account_id},
		fields=["name", "external_unit_id", "external_unit_name", "external_imei", "external_device_id",
			"vehicle", "customer", "tracker"],
		order_by="external_unit_name asc",
	)
	for row in unit_links:
		result["processed"] += 1
		if row.vehicle:
			owner = frappe.db.get_value("Fleet Vehicle", row.vehicle, "customer")
			if owner == account.customer:
				_sync_unit_inventory_assignment(row, account.customer, row.vehicle)
				_ensure_vehicle_hub_assignment(row.vehicle, account.customer, company, row.external_unit_id)
				result["already_linked"].append({"unit_link": row.name, "vehicle": row.vehicle})
			else:
				result["conflicts"].append(_unit_conflict(row, f"Vehicle belongs to {owner or 'another customer'}"))
			continue

		tracker = _tracker_for_unit(row)
		if tracker and tracker.current_customer and tracker.current_customer != account.customer:
			result["conflicts"].append(_unit_conflict(row, f"Tracker belongs to {tracker.current_customer}"))
			continue

		vehicle = tracker.current_vehicle if tracker and tracker.current_vehicle else _matching_fleet_vehicle(
			row.external_unit_name, account.customer
		)
		if vehicle:
			owner = frappe.db.get_value("Fleet Vehicle", vehicle, "customer")
			if owner and owner != account.customer:
				result["conflicts"].append(_unit_conflict(row, f"Matched vehicle belongs to {owner}"))
				continue
		else:
			registration = _vehicle_registration_for_unit(row)
			if frappe.db.exists("Fleet Vehicle", registration):
				owner = frappe.db.get_value("Fleet Vehicle", registration, "customer")
				result["conflicts"].append(_unit_conflict(row, f"Registration already belongs to {owner}"))
				continue
			vehicle_doc = frappe.get_doc({
				"doctype": "Fleet Vehicle", "registration_number": registration,
				"vehicle_name": (row.external_unit_name or registration).strip(), "customer": account.customer,
				"company": company, "vehicle_type": "Other", "status": "Active",
				"notes": f"Created from approved telematics unit {row.external_unit_id}.",
			}).insert(ignore_permissions=True)
			vehicle = vehicle_doc.name
			result["created"].append({"unit_link": row.name, "vehicle": vehicle})

		link = frappe.get_doc("Telematics Unit Link", row.name)
		link.vehicle = vehicle
		link.customer = account.customer
		link.suggested_customer = account.customer
		link.tracker = tracker.name if tracker else link.tracker
		link.sim = _sim_for_tracker(link.tracker, vehicle) if link.tracker else link.sim
		link.status = "Active"
		link.sync_enabled = 1
		link.last_sync_status = "Success"
		link.last_error = None
		link.notes = "Linked automatically after the provider account was approved."
		link.save(ignore_permissions=True)
		_sync_unit_inventory_assignment(link, account.customer, vehicle)
		_ensure_vehicle_hub_assignment(vehicle, account.customer, company, row.external_unit_id)
		result["linked"].append({"unit_link": row.name, "vehicle": vehicle})

	_update_discovered_onboarding_vehicle_state(account, result)
	if commit:
		frappe.db.commit()
	return result


def _tracker_for_unit(unit):
	identifiers = [value for value in (unit.external_imei, unit.external_device_id) if value]
	for identifier in identifiers:
		tracker = frappe.db.get_value(
			"Tracker Profile", {"imei": identifier}, ["name", "current_customer", "current_vehicle"], as_dict=True
		)
		if tracker:
			return tracker
	return None


def _matching_fleet_vehicle(unit_name, customer):
	key = _normalized_vehicle_identifier(unit_name)
	if not key:
		return None
	matches = []
	for vehicle in frappe.get_all("Fleet Vehicle", fields=["name", "registration_number", "vehicle_name", "customer"]):
		if key in {_normalized_vehicle_identifier(vehicle.registration_number), _normalized_vehicle_identifier(vehicle.vehicle_name)}:
			matches.append(vehicle)
	owned = [vehicle for vehicle in matches if vehicle.customer == customer]
	if len(owned) == 1:
		return owned[0].name
	if not owned and len(matches) == 1:
		return matches[0].name
	return None


def _vehicle_registration_for_unit(unit):
	label = re.sub(r"\s+", " ", (unit.external_unit_name or "").strip()).upper()
	return label or f"TELEMATICS-{unit.external_unit_id}"


def _normalized_vehicle_identifier(value):
	return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def _sim_for_tracker(tracker, vehicle):
	assignment = frappe.db.get_value(
		"Tracker SIM Assignment",
		{"tracker": tracker, "status": ["in", ["Prepared", "Reserved", "Assigned", "Installed"]]},
		"sim", order_by="modified desc",
	)
	return assignment or frappe.db.get_value("SIM Profile", {"current_tracker": tracker}, "name")


def _sync_unit_inventory_assignment(unit, customer, vehicle):
	matched_tracker = None if unit.tracker else _tracker_for_unit(unit)
	tracker = unit.tracker or (matched_tracker.name if matched_tracker else None)
	if not tracker:
		return

	frappe.db.set_value(
		"Tracker Profile", tracker,
		{"status": "Assigned", "current_customer": customer, "current_vehicle": vehicle},
		update_modified=False,
	)
	assignment_name = frappe.db.get_value(
		"Tracker SIM Assignment",
		{"tracker": tracker, "status": ["in", ["Prepared", "Reserved", "Assigned", "Installed"]]},
		"name", order_by="modified desc",
	)
	if assignment_name:
		assignment = frappe.get_doc("Tracker SIM Assignment", assignment_name)
		assignment.customer = customer
		assignment.vehicle = vehicle
		if assignment.status in {"Prepared", "Reserved"}:
			assignment.status = "Assigned"
		assignment.notes = "\n".join(filter(None, [assignment.notes, "Assignment context synchronized from Wialon ownership."]))
		assignment.save(ignore_permissions=True)
		frappe.db.set_value("Telematics Unit Link", unit.name, "sim", assignment.sim, update_modified=False)


def _ensure_vehicle_hub_assignment(vehicle, customer, company, external_unit_id):
	existing = frappe.db.get_value(
		"Vehicle Assignment", {"vehicle": vehicle, "customer": customer, "status": "Active"}, "name"
	)
	if existing:
		return existing
	assignment = frappe.get_doc({
		"doctype": "Vehicle Assignment", "status": "Active", "company": company,
		"customer": customer, "vehicle": vehicle, "start_datetime": now_datetime(),
		"primary_assignment": 1,
		"notes": f"Hub ownership synchronized from Wialon unit {external_unit_id}.",
	}).insert(ignore_permissions=True)
	return assignment.name


def _unit_conflict(unit, reason):
	return {"unit_link": unit.name, "unit": unit.external_unit_name or unit.external_unit_id, "reason": reason}


def _update_discovered_onboarding_vehicle_state(account, result):
	if not account.onboarding_job or not result["linked"]:
		return
	job = frappe.get_doc("Omni Onboarding Job", account.onboarding_job)
	job.primary_vehicle = job.primary_vehicle or result["linked"][0]["vehicle"]
	job.vehicles_ready = 1
	job.status = "Vehicle Setup"
	job.next_action = (
		"Review the imported vehicles and telematics links, then prepare or reserve tracker/SIM kits."
		if not result["conflicts"] else
		f"Resolve {len(result['conflicts'])} telematics ownership conflict(s), then prepare tracker/SIM kits."
	)
	for item in job.checklist:
		if item.reference_doctype == "Fleet Vehicle":
			item.status = "Done"
	job.save(ignore_permissions=True)


@frappe.whitelist()
def resolve_discovered_account_duplicate(discovered_account_name, keep_customer, merge_customer=None, activate=1):
	if not frappe.has_permission("Telematics Discovered Account", "write"):
		frappe.throw("Not permitted to resolve duplicate customers.", frappe.PermissionError)
	if not frappe.db.exists("Customer", keep_customer):
		frappe.throw(f"Customer {keep_customer} does not exist.")
	if merge_customer and merge_customer == keep_customer:
		frappe.throw("The customer to merge must be different from the customer being kept.")

	account = frappe.get_doc("Telematics Discovered Account", discovered_account_name)
	if merge_customer:
		if not frappe.db.exists("Customer", merge_customer):
			frappe.throw(f"Customer {merge_customer} does not exist.")
		from omni_operations.omni_setup.customer_merge import get_merged_portal_users, restore_portal_users
		portal_users = get_merged_portal_users(merge_customer, keep_customer)
		_prepare_customer_merge(merge_customer, keep_customer)
		from frappe.model.rename_doc import rename_doc
		rename_doc(
			"Customer", merge_customer, keep_customer, force=True, merge=True,
			ignore_permissions=True, show_alert=False,
		)
		restore_portal_users(keep_customer, portal_users)

	account.reload()
	account.suggested_existing_customer = keep_customer
	account.duplicate_status = "Resolved"
	account.notes = "\n".join(filter(None, [account.notes, f"Duplicate review resolved. Kept customer: {keep_customer}." +
		(f" Merged customer: {merge_customer}." if merge_customer else "")]))
	if account.activation_status == "Activated":
		account.customer = keep_customer
		account.verified_by = frappe.session.user
		account.verified_on = now_datetime()
	account.save(ignore_permissions=True)
	frappe.db.commit()

	if int(activate) and account.activation_status != "Activated":
		return activate_discovered_account(account.name)
	return {"account": account.name, "customer": keep_customer, "merged_customer": merge_customer,
		"status": account.activation_status}


def _prepare_customer_merge(source_customer, target_customer):
	from omni_operations.omni_setup.customer_merge import prepare_customer_fleet_profile_merge
	prepare_customer_fleet_profile_merge(source_customer, target_customer)


@frappe.whitelist()
def sync_provider_units(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	started = now_datetime()
	processed = 0
	created = 0
	updated = 0
	failed = 0
	ignored = 0
	ignored_unit_ids = _ignored_external_unit_ids(provider_account)

	try:
		units = provider.list_units()
		for unit in units:
			processed += 1
			if unit.external_unit_id in ignored_unit_ids:
				ignored += 1
				continue

			unit_link_name = frappe.db.exists(
				"Telematics Unit Link",
				{
					"provider_account": provider_account.name,
					"external_unit_id": unit.external_unit_id,
				},
			)

			if not unit_link_name:
				suggested_customer = _suggested_customer(
					provider_account.name, unit.external_account_id
				)
				frappe.get_doc(
					{
						"doctype": "Telematics Unit Link",
						"provider_account": provider_account.name,
						"external_unit_id": unit.external_unit_id,
						"external_unit_name": unit.external_unit_name,
						"external_creator_id": unit.external_creator_id,
						"external_account_id": unit.external_account_id,
						"suggested_customer": suggested_customer,
						"external_device_id": unit.external_device_id,
						"external_imei": unit.external_imei,
						"external_group": unit.external_group,
						"timezone": unit.timezone,
						"status": "Unlinked",
						"sync_enabled": 0,
						"last_sync_datetime": now_datetime(),
						"last_sync_status": "Warning",
						"notes": "Automatically discovered from provider. Assign the correct Omni vehicle before enabling sync.",
					}
				).insert(ignore_permissions=True)
				created += 1
				continue

			update_values = {
				"external_unit_name": unit.external_unit_name,
				"external_creator_id": unit.external_creator_id,
				"external_account_id": unit.external_account_id,
				"external_device_id": unit.external_device_id,
				"external_imei": unit.external_imei,
				"external_group": unit.external_group,
				"timezone": unit.timezone,
				"last_sync_datetime": now_datetime(),
				"last_sync_status": "Success",
				"last_error": None,
			}
			if not frappe.db.get_value("Telematics Unit Link", unit_link_name, "vehicle"):
				update_values["suggested_customer"] = _suggested_customer(
					provider_account.name, unit.external_account_id
				)
			sync_enabled = frappe.db.get_value("Telematics Unit Link", unit_link_name, "sync_enabled")
			if sync_enabled and unit.position:
				update_values.update(_position_update_values(unit.position))

			frappe.db.set_value(
				"Telematics Unit Link",
				unit_link_name,
				update_values,
			)
			updated += 1

		status = "Success" if failed == 0 else "Warning"
		error_message = None if failed == 0 else f"{failed} provider unit(s) could not be synchronized."
	except Exception as exc:
		status = "Failed"
		error_message = str(exc)

	log = frappe.get_doc(
		{
			"doctype": "Telematics Sync Log",
			"provider_account": provider_account.name,
			"sync_type": "Unit Metadata",
			"status": status,
			"started_datetime": started,
			"finished_datetime": now_datetime(),
			"records_processed": processed,
			"records_created": created,
			"records_updated": updated,
			"records_failed": failed,
			"request_summary": f"Pulled unit metadata from {provider_account.provider}.",
			"response_summary": f"Processed {processed}; discovered {created}; updated {updated}; ignored {ignored}; failed {failed}.",
			"error_message": error_message,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": status,
		"sync_log": log.name,
		"records_processed": processed,
		"records_created": created,
		"records_updated": updated,
		"records_ignored": ignored,
		"records_failed": failed,
}


def _provider_user_values(user):
	flags = user.user_flags
	return {
		"username": user.username,
		"email": user.email,
		"guid": user.guid,
		"creator_id": user.creator_id,
		"creator_username": user.creator_username,
		"account_id": user.account_id,
		"account_name": user.account_name,
		"is_disabled": 1 if flags is not None and flags & 0x01 else 0,
		"is_administrator": 1 if flags is not None and flags & 0x40 else 0,
		"can_create_items": 1 if flags is not None and flags & 0x04 else 0,
		"can_change_settings": 0 if flags is not None and flags & 0x10 else 1,
		"measurement_system": user.measurement_system,
		"access_rights": str(user.access_rights) if user.access_rights is not None else None,
		"host_mask": user.host_mask,
		"last_login": _position_datetime(user.last_login) if user.last_login else None,
		"two_factor_type": str(user.two_factor_type) if user.two_factor_type is not None else None,
		"two_factor_phone": user.two_factor_phone,
		"custom_fields_json": json.dumps(user.custom_fields, indent=2, sort_keys=True) if user.custom_fields else None,
		"admin_fields_json": json.dumps(user.admin_fields, indent=2, sort_keys=True) if user.admin_fields else None,
		"raw_payload_json": json.dumps(user.raw, indent=2, sort_keys=True) if user.raw else None,
		"last_seen": now_datetime(),
	}


def _provider_account_values(account):
	return {
		"account_name": account.account_name, "creator_id": account.creator_id,
		"parent_account_id": account.parent_account_id, "emails": account.emails, "phones": account.phones,
		"guid": account.guid, "access_rights": str(account.access_rights) if account.access_rights is not None else None,
		"custom_fields_json": json.dumps(account.custom_fields, indent=2, sort_keys=True) if account.custom_fields else None,
		"admin_fields_json": json.dumps(account.admin_fields, indent=2, sort_keys=True) if account.admin_fields else None,
		"raw_payload_json": json.dumps(account.raw, indent=2, sort_keys=True) if account.raw else None,
		"last_seen": now_datetime(),
	}


def _discovery_log(provider_account, sync_type, status, started, processed, created, updated, failed, request_summary, error_message):
	return frappe.get_doc({
		"doctype": "Telematics Sync Log", "provider_account": provider_account.name, "sync_type": sync_type,
		"status": status, "started_datetime": started, "finished_datetime": now_datetime(),
		"records_processed": processed, "records_created": created, "records_updated": updated,
		"records_failed": failed, "request_summary": request_summary,
		"response_summary": f"Processed {processed}; created {created}; updated {updated}; failed {failed}.",
		"error_message": error_message,
	}).insert(ignore_permissions=True)


def _refresh_discovered_account_hierarchy(provider_account_name):
	accounts = frappe.get_all(
		"Telematics Discovered Account",
		filters={"provider_account": provider_account_name},
		fields=["name", "external_account_id", "creator_id"],
	)
	users = frappe.get_all(
		"Telematics Discovered User",
		filters={"provider_account": provider_account_name},
		fields=["external_user_id", "creator_id", "account_id"],
	)
	users_by_id = {row.external_user_id: row for row in users}
	accounts_by_id = {row.external_account_id: row for row in accounts}
	root_name = frappe.db.get_value(
		"Telematics Provider Account", provider_account_name, "external_account_name"
	) or provider_account_name
	root_account = next(
		(account for account in accounts if account.external_account_id and account.name and
		 frappe.db.get_value("Telematics Discovered Account", account.name, "account_name").lower() == root_name.lower()),
		None,
	)
	parent_ids = {}
	for account in accounts:
		account_user = users_by_id.get(account.creator_id)
		creator_user = users_by_id.get(account_user.creator_id) if account_user and account_user.creator_id else None
		parent_id = creator_user.account_id if creator_user and creator_user.account_id != account.external_account_id else None
		if not parent_id and root_account and account.external_account_id != root_account.external_account_id:
			parent_id = root_account.external_account_id
		parent_ids[account.external_account_id] = parent_id

	child_counts = {}
	for parent_id in parent_ids.values():
		if parent_id:
			child_counts[parent_id] = child_counts.get(parent_id, 0) + 1

	for account in accounts:
		parent_id = parent_ids.get(account.external_account_id)
		if root_account and account.external_account_id == root_account.external_account_id:
			account_type = "Master Account"
		elif child_counts.get(account.external_account_id):
			account_type = "Regional Admin"
		else:
			account_type = "Customer Hub"
		frappe.db.set_value(
			"Telematics Discovered Account", account.name,
			{
				"parent_account_id": parent_id,
				"parent_account_name": accounts_by_id[parent_id].name if parent_id in accounts_by_id else None,
				"account_type": account_type,
			}, update_modified=False,
		)
	_refresh_duplicate_matches(provider_account_name)


@frappe.whitelist()
def refresh_duplicate_matches(provider_account_name=None):
	provider_accounts = [provider_account_name] if provider_account_name else frappe.get_all(
		"Telematics Provider Account", pluck="name"
	)
	for account_name in provider_accounts:
		_refresh_duplicate_matches(account_name)
	frappe.db.commit()
	return {"provider_accounts": provider_accounts}


def _refresh_duplicate_matches(provider_account_name):
	customers_by_key = {}
	for customer in frappe.get_all("Customer", fields=["name", "customer_name"]):
		key = _normalized_customer_name(customer.customer_name or customer.name)
		customers_by_key.setdefault(key, []).append(customer.name)

	for account in frappe.get_all(
		"Telematics Discovered Account",
		filters={"provider_account": provider_account_name, "account_type": "Customer Hub"},
		fields=["name", "account_name", "customer", "activation_status", "duplicate_status"],
	):
		if account.duplicate_status == "Resolved":
			continue
		matches = sorted(set(customers_by_key.get(_normalized_customer_name(account.account_name), [])))
		exact = next((name for name in matches if name.casefold() == account.account_name.casefold()), None)
		if len(matches) > 1:
			status = "Multiple Matches"
			suggested = min(matches, key=_customer_name_quality)
		elif exact:
			status = "Existing Customer"
			suggested = exact
		elif matches:
			status = "Possible Duplicate"
			suggested = matches[0]
		else:
			status = "No Existing Customer"
			suggested = None
		frappe.db.set_value(
			"Telematics Discovered Account", account.name,
			{
				"duplicate_status": status,
				"suggested_existing_customer": suggested,
				"duplicate_candidates": "\n".join(matches) or None,
			}, update_modified=False,
		)


def _normalized_customer_name(value):
	return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def _customer_name_quality(value):
	return (value.count("_") + value.count("-"), len(value), value.casefold())


@frappe.whitelist()
def check_provider_connection(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	started = now_datetime()

	try:
		is_connected = provider.check_connection()
		status = "Success" if is_connected else "Failed"
		error_message = None if is_connected else "Provider returned an unsuccessful connection check."
	except Exception as exc:
		status = "Failed"
		error_message = str(exc)

	frappe.db.set_value(
		"Telematics Provider Account",
		provider_account.name,
		{
			"last_sync_datetime": now_datetime(),
			"last_sync_status": status,
			"last_error": error_message,
		},
	)
	log = frappe.get_doc(
		{
			"doctype": "Telematics Sync Log",
			"provider_account": provider_account.name,
			"sync_type": "Account Check",
			"status": status,
			"started_datetime": started,
			"finished_datetime": now_datetime(),
			"records_processed": 1,
			"records_updated": 1 if status == "Success" else 0,
			"records_failed": 0 if status == "Success" else 1,
			"request_summary": f"Checked connection for {provider_account.provider}.",
			"response_summary": status,
			"error_message": error_message,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": status,
		"sync_log": log.name,
		"error_message": error_message,
	}


@frappe.whitelist()
def preview_provider_units(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	units = provider.list_units()
	rows = []
	ignored_unit_ids = _ignored_external_unit_ids(provider_account)

	for unit in units:
		is_ignored = unit.external_unit_id in ignored_unit_ids
		unit_link = frappe.db.get_value(
			"Telematics Unit Link",
			{
				"provider_account": provider_account.name,
				"external_unit_id": unit.external_unit_id,
			},
			["name", "vehicle", "customer", "sync_enabled", "last_sync_status"],
			as_dict=True,
		)
		rows.append(
			{
				"external_unit_id": unit.external_unit_id,
				"external_unit_name": unit.external_unit_name,
				"external_creator_id": unit.external_creator_id,
				"external_account_id": unit.external_account_id,
				"external_device_id": unit.external_device_id,
				"external_imei": unit.external_imei,
				"discovered": bool(unit_link),
				"matched": bool(unit_link and unit_link.vehicle),
				"ignored": is_ignored,
				"unit_link": unit_link.name if unit_link else None,
				"vehicle": unit_link.vehicle if unit_link else None,
				"customer": unit_link.customer if unit_link else None,
				"sync_enabled": unit_link.sync_enabled if unit_link else None,
				"last_sync_status": unit_link.last_sync_status if unit_link else None,
			}
		)

	return {
		"provider_account": provider_account.name,
		"provider": provider_account.provider,
		"total_units": len(rows),
		"matched_units": len([row for row in rows if row["matched"]]),
		"ignored_units": len([row for row in rows if row["ignored"]]),
		"unmatched_units": len([row for row in rows if not row["matched"] and not row["ignored"]]),
		"units": rows,
	}


@frappe.whitelist()
def create_provider_unit_links(provider_account_name, links):
	created = []
	updated = []

	for link in links:
		unit_link_name = frappe.db.exists(
			"Telematics Unit Link",
			{
				"provider_account": provider_account_name,
				"external_unit_id": link.get("external_unit_id"),
			},
		)
		values = {
			"vehicle": link.get("vehicle"),
			"external_unit_name": link.get("external_unit_name"),
			"sync_enabled": link.get("sync_enabled", 1),
			"status": link.get("status", "Active"),
		}

		if unit_link_name:
			frappe.db.set_value("Telematics Unit Link", unit_link_name, values)
			updated.append(unit_link_name)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Telematics Unit Link",
				"provider_account": provider_account_name,
				"vehicle": link.get("vehicle"),
				"external_unit_id": link.get("external_unit_id"),
				"external_unit_name": link.get("external_unit_name"),
				"sync_enabled": link.get("sync_enabled", 1),
				"status": link.get("status", "Active"),
			}
		).insert()
		created.append(doc.name)

	frappe.db.commit()

	return {
		"created": created,
		"updated": updated,
	}


@frappe.whitelist()
def sync_vehicle_telematics(vehicle):
	unit_links = frappe.get_all(
		"Telematics Unit Link",
		filters={"vehicle": vehicle, "sync_enabled": 1},
		pluck="provider_account",
	)
	results = []

	for provider_account in sorted(set(unit_links)):
		results.append(sync_provider_units(provider_account))

	return results


def _position_update_values(position):
	update_values = {}

	if position.get("latitude") is not None:
		update_values["latitude"] = position.get("latitude")
	if position.get("longitude") is not None:
		update_values["longitude"] = position.get("longitude")
	if position.get("speed") is not None:
		update_values["speed"] = position.get("speed")
	if position.get("ignition") is not None:
		update_values["ignition"] = position.get("ignition")
	if position.get("odometer") is not None:
		update_values["odometer"] = position.get("odometer")
	if position.get("timestamp"):
		update_values["last_position_datetime"] = _position_datetime(position.get("timestamp"))

	return update_values


def _position_datetime(value):
	if isinstance(value, (int, float)):
		return get_datetime(datetime.fromtimestamp(value))
	return get_datetime(value)


def _ignored_external_unit_ids(provider_account):
	raw_value = provider_account.get("ignored_external_unit_ids") or ""
	return {unit_id.strip() for unit_id in raw_value.replace(",", "\n").splitlines() if unit_id.strip()}


def _suggested_customer(provider_account_name, external_account_id):
	if not external_account_id or not frappe.db.exists("DocType", "Telematics Discovered Account"):
		return None
	return frappe.db.get_value(
		"Telematics Discovered Account",
		{
			"provider_account": provider_account_name,
			"external_account_id": external_account_id,
			"activation_status": "Activated",
		},
		"customer",
	)
