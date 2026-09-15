import frappe


def on_sales_invoice_submit(doc, method=None):
	account_name = frappe.db.get_value(
		"Fiscal Provider Account",
		{"company": doc.company, "status": "Active", "auto_fiscalise_sales_invoices": 1},
		"name",
	)
	if not account_name:
		return

	from omni_operations.fiscalisation.service import fiscalise_sales_invoice

	fiscalise_sales_invoice(doc.name, account_name)
