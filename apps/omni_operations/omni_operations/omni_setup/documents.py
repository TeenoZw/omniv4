import frappe

from omni_operations.omni_setup.hub_companies import get_company_for_hub_customer


def ensure_sample_fleet_documents():
	vehicle = "AHG-9216"
	customer = "Mapanje Hub"
	if not frappe.db.exists("Fleet Vehicle", vehicle):
		return {"created": [], "skipped": f"{vehicle} not found"}

	file_url = ensure_sample_file()
	doc_name = frappe.db.exists(
		"Fleet Document",
		{
			"customer": customer,
			"vehicle": vehicle,
			"document_type": "Vehicle Registration",
			"title": "AHG-9216 Registration",
		},
	)

	if doc_name:
		doc = frappe.get_doc("Fleet Document", doc_name)
		created = []
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Fleet Document",
				"title": "AHG-9216 Registration",
				"document_type": "Vehicle Registration",
				"customer": customer,
				"vehicle": vehicle,
				"company": get_company_for_hub_customer(customer),
			}
		)
		created = [doc.title]

	doc.status = "Active"
	doc.reference_number = "AHG-9216"
	doc.portal_visible = 1
	doc.attachment = file_url
	doc.notes = "Portal-visible vehicle registration document for customer document workflow verification."

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	frappe.db.commit()
	return {"created": created, "document": doc.name, "file_url": file_url}


def ensure_sample_file():
	file_name = "omni-ahg-9216-registration.txt"
	existing = frappe.db.get_value("File", {"file_name": file_name}, "file_url")
	if existing:
		return existing

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": "Vehicle registration document placeholder for Omni customer portal verification.",
			"is_private": 0,
		}
	)
	file_doc.insert(ignore_permissions=True)
	return file_doc.file_url
