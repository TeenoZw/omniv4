from __future__ import annotations

import frappe

from omni_operations.telematics.providers.base import BaseTelematicsProvider, ProviderUnit


class DemoTelematicsProvider(BaseTelematicsProvider):
	def check_connection(self) -> bool:
		return bool(self.provider_account.name)

	def list_units(self) -> list[ProviderUnit]:
		existing_links = frappe.get_all(
			"Telematics Unit Link",
			filters={"provider_account": self.provider_account.name},
			fields=["external_unit_id", "external_unit_name", "external_device_id", "external_imei"],
		)

		if existing_links:
			return [
				ProviderUnit(
					external_unit_id=link.external_unit_id,
					external_unit_name=link.external_unit_name or link.external_unit_id,
					external_device_id=link.external_device_id,
					external_imei=link.external_imei,
					external_group="Demo Fleet",
					timezone="Africa/Harare",
					raw={"source": "demo_adapter"},
				)
				for link in existing_links
			]

		return [
			ProviderUnit(
				external_unit_id="demo-unit-001",
				external_unit_name="Demo Unit 001",
				external_group="Demo Fleet",
				timezone="Africa/Harare",
				raw={"source": "demo_adapter"},
			)
		]

	def get_latest_position(self, external_unit_id: str) -> dict:
		return {
			"external_unit_id": external_unit_id,
			"latitude": -17.8252,
			"longitude": 31.0335,
			"speed": 0,
			"ignition": 0,
			"odometer": None,
		}
