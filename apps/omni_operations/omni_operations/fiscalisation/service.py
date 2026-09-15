import frappe
from frappe.utils import now_datetime

from omni_operations.fiscalisation.providers.registry import get_provider


@frappe.whitelist()
def fiscalise_sales_invoice(sales_invoice_name, provider_account_name=None):
	sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
	if sales_invoice.docstatus != 1:
		frappe.throw("Only submitted Sales Invoices can be fiscalised.")

	provider_account_name = provider_account_name or frappe.db.get_value(
		"Fiscal Provider Account",
		{"company": sales_invoice.company, "status": "Active"},
		"name",
	)
	if not provider_account_name:
		frappe.throw("No active Fiscal Provider Account found.")

	provider_account = frappe.get_doc("Fiscal Provider Account", provider_account_name)
	fiscal_device = get_default_fiscal_device(provider_account.name, sales_invoice.company)
	fiscal_day = get_open_fiscal_day(fiscal_device)

	existing = frappe.db.exists(
		"Fiscal Document",
		{"sales_invoice": sales_invoice.name, "docstatus": ["<", 2]},
	)
	if existing:
		fiscal_document = frappe.get_doc("Fiscal Document", existing)
	else:
		document_type = "Credit Note" if sales_invoice.is_return else "Fiscal Invoice"
		fiscal_document = frappe.get_doc(
			{
				"doctype": "Fiscal Document",
				"provider_account": provider_account.name,
				"fiscal_device": fiscal_device.name,
				"fiscal_day": fiscal_day.name,
				"source_doctype": "Sales Invoice",
				"sales_invoice": sales_invoice.name,
				"document_type": document_type,
				"customer": sales_invoice.customer,
				"company": sales_invoice.company,
				"grand_total": sales_invoice.grand_total,
				"tax_total": sales_invoice.total_taxes_and_charges,
				"status": "Pending",
			}
		).insert(ignore_permissions=True)

	try:
		provider = get_provider(provider_account, fiscal_device)
		result = provider.submit_invoice(sales_invoice, fiscal_day)
		fiscal_document.update(result)
		fiscal_document.save(ignore_permissions=True)
		fiscal_device.db_set("last_receipt_counter", result["receipt_counter"])
		fiscal_day.db_set("last_receipt_counter", result["receipt_counter"])
		create_fiscal_sync_log(provider_account, fiscal_device, fiscal_document, "Success", result["provider_response"])
	except Exception as exc:
		fiscal_document.db_set("status", "Failed")
		fiscal_document.db_set("error_message", str(exc))
		create_fiscal_sync_log(provider_account, fiscal_device, fiscal_document, "Failed", None, str(exc))
		raise

	frappe.db.commit()
	return fiscal_document.name


def get_default_fiscal_device(provider_account_name, company):
	device_name = frappe.db.get_value(
		"Fiscal Device",
		{"provider_account": provider_account_name, "company": company, "status": "Active"},
		"name",
	)
	if not device_name:
		frappe.throw("No active Fiscal Device found.")
	return frappe.get_doc("Fiscal Device", device_name)


def get_open_fiscal_day(fiscal_device):
	day_name = frappe.db.get_value(
		"Fiscal Day",
		{"fiscal_device": fiscal_device.name, "status": "Open"},
		"name",
	)
	if day_name:
		return frappe.get_doc("Fiscal Day", day_name)

	fiscal_day = frappe.get_doc(
		{
			"doctype": "Fiscal Day",
			"provider_account": fiscal_device.provider_account,
			"fiscal_device": fiscal_device.name,
			"company": fiscal_device.company,
			"day_number": (fiscal_device.current_fiscal_day or 0) + 1,
			"status": "Open",
			"opened_datetime": now_datetime(),
		}
	).insert(ignore_permissions=True)
	fiscal_device.db_set("current_fiscal_day", fiscal_day.day_number)
	return fiscal_day


def create_fiscal_sync_log(provider_account, fiscal_device, fiscal_document, status, response_summary=None, error_message=None):
	return frappe.get_doc(
		{
			"doctype": "Fiscal Sync Log",
			"provider_account": provider_account.name,
			"fiscal_device": fiscal_device.name,
			"fiscal_document": fiscal_document.name,
			"sync_type": "Submit Invoice",
			"status": status,
			"started_datetime": now_datetime(),
			"finished_datetime": now_datetime(),
			"response_summary": response_summary,
			"error_message": error_message,
		}
	).insert(ignore_permissions=True)
