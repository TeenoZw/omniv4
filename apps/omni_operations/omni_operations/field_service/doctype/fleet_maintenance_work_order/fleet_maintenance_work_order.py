import frappe
from frappe.model.document import Document
from frappe.utils import add_days, nowdate


class FleetMaintenanceWorkOrder(Document):
	def validate(self):
		self.set_customer_from_vehicle()
		self.calculate_parts_total()
		self.calculate_total_amount()

	def set_customer_from_vehicle(self):
		if self.vehicle and not self.customer:
			self.customer = frappe.db.get_value("Fleet Vehicle", self.vehicle, "customer")

	def calculate_parts_total(self):
		total = 0
		for part in self.parts_used:
			part.amount = (part.qty or 0) * (part.rate or 0)
			total += part.amount
		self.parts_total = total

	def calculate_total_amount(self):
		self.total_amount = (self.parts_total or 0) + (self.labour_amount or 0)

	@frappe.whitelist()
	def create_stock_entry(self):
		if self.stock_entry:
			return self.stock_entry

		if not self.parts_used:
			frappe.throw("Add parts before creating a stock entry.")

		stock_entry = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Issue",
				"company": self.company,
				"posting_date": nowdate(),
				"remarks": f"Parts used for {self.name}",
				"items": [
					{
						"item_code": part.item_code,
						"qty": part.qty,
						"s_warehouse": part.source_warehouse,
					}
					for part in self.parts_used
				],
			}
		).insert(ignore_permissions=True)
		stock_entry.submit()
		self.db_set("stock_entry", stock_entry.name)
		self.db_set("parts_stock_status", "Issued")
		return stock_entry.name

	@frappe.whitelist()
	def create_sales_invoice(self):
		if self.sales_invoice:
			return self.sales_invoice

		items = []
		if self.labour_amount:
			items.append({"item_code": "MAINT-LABOUR", "qty": 1, "rate": self.labour_amount})

		for part in self.parts_used:
			items.append({"item_code": part.item_code, "qty": part.qty, "rate": part.rate})

		if not items:
			frappe.throw("Add labour or parts before creating an invoice.")

		invoice = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"customer": self.customer,
				"company": self.company,
				"title": f"Maintenance Invoice - {self.vehicle}",
				"due_date": add_days(nowdate(), 14),
				"items": items,
			}
		).insert(ignore_permissions=True)
		invoice.submit()
		self.db_set("sales_invoice", invoice.name)
		self.db_set("billing_status", "Invoiced")
		return invoice.name
