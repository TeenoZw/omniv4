from frappe.utils import now_datetime


class DemoZimraFDMSProvider:
	def __init__(self, provider_account, fiscal_device):
		self.provider_account = provider_account
		self.fiscal_device = fiscal_device

	def submit_invoice(self, sales_invoice, fiscal_day=None):
		counter = (self.fiscal_device.last_receipt_counter or 0) + 1
		receipt_number = f"DEMO-ZIMRA-{sales_invoice.name}-{counter:06d}"
		return {
			"status": "Fiscalised",
			"fiscal_receipt_number": receipt_number,
			"receipt_counter": counter,
			"qr_data": f"ZIMRA-DEMO|{self.provider_account.taxpayer_tin or 'TIN'}|{receipt_number}|{sales_invoice.grand_total}",
			"verification_url": f"https://fdms.zimra.co.zw/demo/verify/{receipt_number}",
			"provider_response": "Demo ZIMRA FDMS fiscalisation accepted.",
			"submitted_datetime": now_datetime(),
			"fiscal_day": fiscal_day.name if fiscal_day else None,
		}
