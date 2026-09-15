import frappe
from frappe.utils import add_days, nowdate

from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

from omni_operations.omni_setup.hub_companies import get_company_for_hub_customer, get_default_hub_company
from omni_operations.omni_setup.items import ensure_fleet_service_items


FLEET_STARTER_LINES = [
	{"item_code": "TRACKER-HW-4G", "qty": 1, "rate": 120},
	{"item_code": "SIM-IOT", "qty": 1, "rate": 15},
	{"item_code": "INSTALL-LABOUR", "qty": 1, "rate": 60},
	{"item_code": "FLEET-MONTHLY-SERVICE", "qty": 1, "rate": 35},
]

DEMO_QUOTATION_TITLE = "Omni Fleet Starter Quote - Demo"
DEMO_SALES_ORDER_TITLE = "Omni Fleet Starter Order - Demo"
DEMO_SALES_INVOICE_TITLE = "Omni Fleet Starter Invoice - Demo"


def get_default_company():
	return get_default_hub_company()


def get_working_customer_and_company(customer=None, company=None):
	customer = customer or frappe.db.get_value("Customer Fleet Profile", {}, "customer", order_by="modified desc")
	if not customer:
		frappe.throw("Create a Customer Fleet Profile before running commercial workflow helpers.")
	company = company or get_company_for_hub_customer(customer)
	if not company:
		frappe.throw(f"No Omni accounting company could be resolved for customer {customer}.")
	return customer, company


def get_receivable_account(company):
	return frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Receivable", "is_group": 0},
		"name",
	)


def get_bank_or_cash_account(company):
	return frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Bank", "is_group": 0},
		"name",
	) or frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Cash", "is_group": 0},
		"name",
	)


@frappe.whitelist()
def ensure_fleet_item_prices(price_list="Standard Selling"):
	ensure_fleet_service_items()
	created = []
	updated = []

	for line in FLEET_STARTER_LINES:
		existing = frappe.db.exists(
			"Item Price",
			{
				"item_code": line["item_code"],
				"price_list": price_list,
				"selling": 1,
				"currency": "USD",
			},
		)

		if existing:
			item_price = frappe.get_doc("Item Price", existing)
			item_price.price_list_rate = line["rate"]
			item_price.save(ignore_permissions=True)
			updated.append(existing)
		else:
			item_price = frappe.get_doc(
				{
					"doctype": "Item Price",
					"item_code": line["item_code"],
					"price_list": price_list,
					"selling": 1,
					"currency": "USD",
					"price_list_rate": line["rate"],
				}
			).insert(ignore_permissions=True)
			created.append(item_price.name)

	frappe.db.commit()
	return {"created": created, "updated": updated}


@frappe.whitelist()
def create_fleet_starter_quotation(customer=None, company=None):
	customer, company = get_working_customer_and_company(customer, company)
	ensure_fleet_item_prices()

	existing = frappe.db.exists(
		"Quotation",
		{
			"title": DEMO_QUOTATION_TITLE,
			"quotation_to": "Customer",
			"party_name": customer,
			"company": company,
			"docstatus": ["<", 2],
		},
	)

	if existing:
		return existing

	quotation = frappe.get_doc(
		{
			"doctype": "Quotation",
			"title": DEMO_QUOTATION_TITLE,
			"quotation_to": "Customer",
			"party_name": customer,
			"company": company,
			"transaction_date": nowdate(),
			"valid_till": add_days(nowdate(), 30),
			"order_type": "Sales",
			"items": [
				{
					"item_code": line["item_code"],
					"qty": line["qty"],
					"rate": line["rate"],
				}
				for line in FLEET_STARTER_LINES
			],
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	return quotation.name


@frappe.whitelist()
def validate_quote_to_invoice_flow(customer=None, company=None):
	customer, company = get_working_customer_and_company(customer, company)
	quotation_name = create_fleet_starter_quotation(customer, company)
	quotation = frappe.get_doc("Quotation", quotation_name)
	if quotation.docstatus == 0:
		quotation.submit()

	sales_order_name = frappe.db.exists(
		"Sales Order",
		{"title": DEMO_SALES_ORDER_TITLE, "customer": customer, "company": company, "docstatus": ["<", 2]},
	)
	if sales_order_name:
		sales_order = frappe.get_doc("Sales Order", sales_order_name)
	else:
		sales_order = make_sales_order(quotation.name)
		sales_order.title = DEMO_SALES_ORDER_TITLE
		sales_order.delivery_date = add_days(nowdate(), 7)
		for item in sales_order.items:
			item.delivery_date = sales_order.delivery_date
		sales_order.insert(ignore_permissions=True)

	if sales_order.docstatus == 0:
		sales_order.submit()

	sales_invoice_name = frappe.db.exists(
		"Sales Invoice",
		{"title": DEMO_SALES_INVOICE_TITLE, "customer": customer, "company": company, "docstatus": ["<", 2]},
	)
	if sales_invoice_name:
		sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
	else:
		sales_invoice = make_sales_invoice(sales_order.name)
		sales_invoice.title = DEMO_SALES_INVOICE_TITLE
		sales_invoice.due_date = add_days(nowdate(), 14)
		sales_invoice.insert(ignore_permissions=True)

	if sales_invoice.docstatus == 0:
		sales_invoice.submit()

	frappe.db.commit()
	return {
		"quotation": quotation.name,
		"sales_order": sales_order.name,
		"sales_invoice": sales_invoice.name,
		"grand_total": sales_invoice.grand_total,
		"outstanding_amount": sales_invoice.outstanding_amount,
	}


@frappe.whitelist()
def validate_payment_capture(customer=None, company=None):
	customer, company = get_working_customer_and_company(customer, company)
	flow = validate_quote_to_invoice_flow(customer, company)
	sales_invoice = frappe.get_doc("Sales Invoice", flow["sales_invoice"])

	existing_payment = frappe.db.exists(
		"Payment Entry Reference",
		{
			"reference_doctype": "Sales Invoice",
			"reference_name": sales_invoice.name,
		},
	)
	if existing_payment:
		payment_name = frappe.db.get_value("Payment Entry Reference", existing_payment, "parent")
		payment_entry = frappe.get_doc("Payment Entry", payment_name)
	else:
		payment_entry = get_payment_entry("Sales Invoice", sales_invoice.name)
		payment_entry.paid_to = get_bank_or_cash_account(company)
		payment_entry.party_type = "Customer"
		payment_entry.party = customer
		payment_entry.reference_no = f"OMNI-{sales_invoice.name}"
		payment_entry.reference_date = nowdate()
		payment_entry.insert(ignore_permissions=True)

	if payment_entry.docstatus == 0:
		payment_entry.submit()

	refresh_customer_fleet_profile_commercial(customer, company)
	frappe.db.commit()
	sales_invoice.reload()
	return {
		**flow,
		"payment_entry": payment_entry.name,
		"paid_amount": payment_entry.paid_amount,
		"invoice_outstanding": sales_invoice.outstanding_amount,
	}


def get_customer_commercial_summary(customer, company=None):
	filters = {"customer": customer, "docstatus": 1}
	if company:
		filters["company"] = company

	latest_invoice = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=["name", "status", "grand_total", "outstanding_amount", "posting_date"],
		order_by="posting_date desc, creation desc",
		limit=1,
	)

	if not latest_invoice:
		return {
			"latest_sales_invoice": None,
			"invoice_status": None,
			"invoice_grand_total": 0,
			"invoice_outstanding_amount": 0,
			"latest_payment_entry": None,
			"last_payment_amount": 0,
			"last_payment_date": None,
		}

	invoice = latest_invoice[0]
	payment_reference = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Invoice", "reference_name": invoice.name},
		fields=["parent"],
		order_by="creation desc",
		limit=1,
	)
	payment_entry = None
	if payment_reference:
		payment_entry = frappe.db.get_value(
			"Payment Entry",
			payment_reference[0].parent,
			["name", "paid_amount", "posting_date"],
			as_dict=True,
		)

	return {
		"latest_sales_invoice": invoice.name,
		"invoice_status": invoice.status,
		"invoice_grand_total": invoice.grand_total,
		"invoice_outstanding_amount": invoice.outstanding_amount,
		"latest_payment_entry": payment_entry.name if payment_entry else None,
		"last_payment_amount": payment_entry.paid_amount if payment_entry else 0,
		"last_payment_date": payment_entry.posting_date if payment_entry else None,
	}


@frappe.whitelist()
def refresh_customer_fleet_profile_commercial(customer=None, company=None):
	customer, company = get_working_customer_and_company(customer, company)
	profile_name = frappe.db.exists("Customer Fleet Profile", customer)
	if not profile_name:
		return {"updated": False, "reason": "Customer Fleet Profile not found"}

	profile = frappe.get_doc("Customer Fleet Profile", profile_name)
	profile.update(get_customer_commercial_summary(customer, company))
	profile.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"updated": True,
		"profile": profile.name,
		"latest_sales_invoice": profile.latest_sales_invoice,
		"invoice_status": profile.invoice_status,
		"invoice_outstanding_amount": profile.invoice_outstanding_amount,
		"latest_payment_entry": profile.latest_payment_entry,
	}
