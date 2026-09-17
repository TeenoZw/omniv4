from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any

import frappe
import requests

from omni_operations.telematics.providers.base import BaseTelematicsProvider, ProviderAccount, ProviderUnit, ProviderUser


DEFAULT_WIALON_HOST = "https://hst-api.wialon.com"
UNIT_DISCOVERY_FLAGS = 1285
USER_DISCOVERY_FLAGS = 463
ACCOUNT_DISCOVERY_FLAGS = 207


class WialonTelematicsProvider(BaseTelematicsProvider):
	def check_connection(self) -> bool:
		with self._session() as sid:
			return bool(sid)

	def list_units(self) -> list[ProviderUnit]:
		with self._session() as sid:
			payload = self._request(
				"core/search_items",
				{
					"spec": {
						"itemsType": "avl_unit",
						"propName": "sys_name",
						"propValueMask": "*",
						"sortType": "sys_name",
					},
					"force": 1,
					"flags": UNIT_DISCOVERY_FLAGS,
					"from": 0,
					"to": 0,
				},
				sid=sid,
			)

		return [self._to_provider_unit(unit) for unit in payload.get("items", [])]

	def list_users(self) -> list[ProviderUser]:
		with self._session() as sid:
			payload = self._request(
				"core/search_items",
				{
					"spec": {
						"itemsType": "user",
						"propName": "sys_name",
						"propValueMask": "*",
						"sortType": "sys_name",
					},
					"force": 1,
					"flags": USER_DISCOVERY_FLAGS,
					"from": 0,
					"to": 0,
				},
				sid=sid,
			)

			try:
				accounts_payload = self._request(
					"core/search_items",
					{
						"spec": {
							"itemsType": "avl_resource",
							"propName": "rel_is_account",
							"propValueMask": "1",
							"sortType": "sys_name",
						},
						"force": 1,
						"flags": 5,
						"from": 0,
						"to": 0,
					},
					sid=sid,
				)
			except Exception:
				accounts_payload = {"items": []}

		users = payload.get("items", [])
		user_names = {str(user.get("id")): user.get("nm") for user in users if user.get("id") is not None}
		account_names = {
			str(account.get("id")): account.get("nm")
			for account in accounts_payload.get("items", [])
			if account.get("id") is not None
		}
		return [self._to_provider_user(user, user_names, account_names) for user in users]

	def list_accounts(self) -> list[ProviderAccount]:
		with self._session() as sid:
			payload = self._request(
				"core/search_items",
				{
					"spec": {
						"itemsType": "avl_resource",
						"propName": "rel_is_account",
						"propValueMask": "1",
						"sortType": "sys_name",
					},
					"force": 1,
					"flags": ACCOUNT_DISCOVERY_FLAGS,
					"from": 0,
					"to": 0,
				},
				sid=sid,
			)
		return [self._to_provider_account(account) for account in payload.get("items", [])]

	def get_latest_position(self, external_unit_id: str) -> dict[str, Any]:
		with self._session() as sid:
			payload = self._request(
				"core/search_item",
				{"id": int(external_unit_id), "flags": UNIT_DISCOVERY_FLAGS},
				sid=sid,
			)

		unit = payload.get("item") or {}
		return self._position_from_unit(unit)

	@contextmanager
	def _session(self):
		sid = self._login()
		try:
			yield sid
		finally:
			if sid:
				try:
					self._request("core/logout", {}, sid=sid)
				except Exception:
					pass

	def _login(self) -> str:
		token = self._password("access_token")
		if not token:
			frappe.throw("Access Token is required for Wialon telematics accounts.")

		payload = self._request("token/login", {"token": token}, sid=None)
		sid = payload.get("eid") or payload.get("sid")
		if not sid:
			frappe.throw("Wialon login did not return a session id.")
		return sid

	def _request(self, service: str, params: dict[str, Any], sid: str | None = None) -> dict[str, Any]:
		base_url = (self.provider_account.api_base_url or DEFAULT_WIALON_HOST).rstrip("/")
		query = {
			"svc": service,
			"params": json.dumps(params),
		}
		if sid:
			query["sid"] = sid

		response = requests.post(
			f"{base_url}/wialon/ajax.html",
			data=query,
			headers={"Content-Type": "application/x-www-form-urlencoded"},
			timeout=30,
		)
		response.raise_for_status()
		payload = response.json()
		if isinstance(payload, dict) and payload.get("error"):
			frappe.throw(f"Wialon API error {payload.get('error')} for {service}.")
		return payload

	def _password(self, fieldname: str) -> str | None:
		try:
			return self.provider_account.get_password(fieldname, raise_exception=False)
		except TypeError:
			pass

		if self.provider_account.get(fieldname):
			return self.provider_account.get_password(fieldname)
		return None

	def _to_provider_unit(self, unit: dict[str, Any]) -> ProviderUnit:
		external_unit_id = unit.get("id")
		if external_unit_id is None:
			frappe.throw("Wialon unit payload did not include id.")

		return ProviderUnit(
			external_unit_id=str(external_unit_id),
			external_unit_name=unit.get("nm"),
			external_creator_id=str(unit.get("crt")) if unit.get("crt") is not None else None,
			external_account_id=str(unit.get("bact")) if unit.get("bact") is not None else None,
			external_device_id=str(unit.get("uid")) if unit.get("uid") else None,
			external_imei=str(unit.get("uid")) if unit.get("uid") else None,
			external_group=None,
			timezone=None,
			position=self._position_from_unit(unit),
			raw=unit,
		)

	def _to_provider_user(
		self, user: dict[str, Any], user_names: dict[str, str], account_names: dict[str, str]
	) -> ProviderUser:
		external_user_id = user.get("id")
		if external_user_id is None:
			frappe.throw("Wialon user payload did not include id.")

		properties = user.get("prp") or {}
		two_factor = user.get("ap") or {}
		creator_id = str(user.get("crt")) if user.get("crt") is not None else None
		account_id = str(user.get("bact")) if user.get("bact") is not None else None
		return ProviderUser(
			external_user_id=str(external_user_id),
			username=user.get("nm") or str(external_user_id),
			creator_id=creator_id,
			creator_username=user_names.get(creator_id),
			account_id=account_id,
			account_name=account_names.get(account_id),
			email=properties.get("email"),
			last_login=user.get("ld"),
			user_flags=user.get("fl"),
			access_rights=user.get("uacl"),
			measurement_system=user.get("mu"),
			guid=user.get("gd"),
			host_mask=user.get("hm"),
			two_factor_type=two_factor.get("type"),
			two_factor_phone=two_factor.get("phone"),
			custom_fields=user.get("flds"),
			admin_fields=user.get("aflds"),
			raw=user,
		)

	def _to_provider_account(self, account: dict[str, Any]) -> ProviderAccount:
		external_account_id = account.get("id")
		if external_account_id is None:
			frappe.throw("Wialon account payload did not include id.")
		properties = account.get("prp") or {}
		return ProviderAccount(
			external_account_id=str(external_account_id),
			account_name=account.get("nm") or str(external_account_id),
			creator_id=str(account.get("crt")) if account.get("crt") is not None else None,
			parent_account_id=None,
			emails=properties.get("emails"),
			phones=properties.get("phones"),
			guid=account.get("gd"),
			access_rights=account.get("uacl"),
			custom_fields=account.get("flds"),
			admin_fields=account.get("aflds"),
			raw=account,
		)

	def _position_from_unit(self, unit: dict[str, Any]) -> dict[str, Any]:
		position = unit.get("pos") or (unit.get("lmsg") or {}).get("pos") or {}
		return {
			"external_unit_id": str(unit.get("id")) if unit.get("id") is not None else None,
			"external_unit_name": unit.get("nm"),
			"latitude": position.get("y"),
			"longitude": position.get("x"),
			"speed": position.get("s"),
			"course": position.get("c"),
			"altitude": position.get("z"),
			"timestamp": unit.get("t") or (unit.get("lmsg") or {}).get("t"),
			"raw": unit,
		}
