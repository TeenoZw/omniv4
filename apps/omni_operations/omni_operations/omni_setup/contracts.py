import frappe
from frappe.utils import nowdate

from omni_operations.omni_setup.hub_companies import get_company_for_hub_customer
from omni_operations.omni_setup.items import ensure_fleet_service_items


def ensure_sample_fleet_contracts():
	customer = "Mapanje Hub"
	vehicle = "AHG-9216"
	if not frappe.db.exists("Customer", customer):
		return {"created": [], "skipped": f"{customer} customer not found"}

	ensure_fleet_service_items()
	contract_name = frappe.db.exists(
		"Fleet Contract",
		{
			"customer": customer,
			"vehicle": vehicle,
			"contract_title": "Mapanje Hub Monthly Fleet Tracking",
		},
	)

	if contract_name:
		contract = frappe.get_doc("Fleet Contract", contract_name)
		created = []
	else:
		contract = frappe.get_doc(
			{
				"doctype": "Fleet Contract",
				"contract_title": "Mapanje Hub Monthly Fleet Tracking",
				"customer": customer,
				"company": get_company_for_hub_customer(customer),
				"vehicle": vehicle if frappe.db.exists("Fleet Vehicle", vehicle) else None,
				"service_item": "FLEET-MONTHLY-SERVICE",
				"start_date": nowdate(),
			}
		)
		created = [contract.contract_title]

	contract.status = "Active"
	contract.billing_frequency = "Monthly"
	contract.monthly_rate = 35
	contract.contract_value = 35
	contract.billing_status = "Current"
	contract.portal_visible = 1
	contract.notes = "Contract created to verify customer portal contract visibility."

	if contract.is_new():
		contract.insert(ignore_permissions=True)
	else:
		contract.save(ignore_permissions=True)

	frappe.db.commit()
	return {"created": created, "contract": contract.name}
