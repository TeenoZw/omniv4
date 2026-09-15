import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class TelematicsSyncLog(Document):
	def validate(self):
		self.set_provider_from_account()
		self.set_finished_datetime()

	def after_insert(self):
		self.update_sync_health()

	def set_provider_from_account(self):
		if self.provider_account:
			self.provider = frappe.db.get_value("Telematics Provider Account", self.provider_account, "provider")

	def set_finished_datetime(self):
		if self.status in ("Success", "Warning", "Failed") and not self.finished_datetime:
			self.finished_datetime = now_datetime()

	def update_sync_health(self):
		update_values = {
			"last_sync_datetime": self.finished_datetime or self.started_datetime or now_datetime(),
			"last_sync_status": self.status,
			"last_error": self.error_message if self.status == "Failed" else None,
		}

		if self.provider_account:
			frappe.db.set_value("Telematics Provider Account", self.provider_account, update_values)

		if self.unit_link:
			frappe.db.set_value("Telematics Unit Link", self.unit_link, update_values)
