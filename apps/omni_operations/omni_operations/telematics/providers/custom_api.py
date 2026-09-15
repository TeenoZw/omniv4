from __future__ import annotations

import requests
import frappe

from omni_operations.telematics.providers.base import BaseTelematicsProvider, ProviderUnit


class CustomAPITelematicsProvider(BaseTelematicsProvider):
	def check_connection(self) -> bool:
		response = self._request("GET", "/health")
		return response.status_code < 400

	def list_units(self) -> list[ProviderUnit]:
		response = self._request("GET", "/units")
		payload = response.json()
		units = payload.get("units", payload if isinstance(payload, list) else [])
		return [self._to_provider_unit(unit) for unit in units]

	def get_latest_position(self, external_unit_id: str) -> dict:
		response = self._request("GET", f"/units/{external_unit_id}/position")
		return response.json()

	def _request(self, method: str, path: str):
		base_url = (self.provider_account.api_base_url or "").rstrip("/")
		if not base_url:
			frappe.throw("API Base URL is required for Custom API telematics accounts.")

		headers = {}
		auth = None
		auth_type = self.provider_account.auth_type

		if auth_type == "API Token":
			token = self._password("access_token")
			if token:
				headers["Authorization"] = f"Bearer {token}"
		elif auth_type == "Username and Password":
			password = self._password("password")
			auth = (self.provider_account.username, password)

		response = requests.request(
			method,
			f"{base_url}{path}",
			headers=headers,
			auth=auth,
			timeout=30,
		)
		response.raise_for_status()
		return response

	def _password(self, fieldname: str) -> str | None:
		if not self.provider_account.get(fieldname):
			return None
		return self.provider_account.get_password(fieldname)

	def _to_provider_unit(self, unit: dict) -> ProviderUnit:
		external_unit_id = unit.get("external_unit_id") or unit.get("id") or unit.get("unit_id")
		if not external_unit_id:
			frappe.throw("Custom API unit payload must include external_unit_id, id, or unit_id.")

		return ProviderUnit(
			external_unit_id=str(external_unit_id),
			external_unit_name=unit.get("external_unit_name") or unit.get("name"),
			external_device_id=unit.get("external_device_id") or unit.get("device_id"),
			external_imei=unit.get("external_imei") or unit.get("imei"),
			external_group=unit.get("external_group") or unit.get("group"),
			timezone=unit.get("timezone"),
			raw=unit,
		)

