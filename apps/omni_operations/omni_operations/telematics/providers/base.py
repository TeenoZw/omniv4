from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderUnit:
	external_unit_id: str
	external_unit_name: str | None = None
	external_creator_id: str | None = None
	external_account_id: str | None = None
	external_device_id: str | None = None
	external_imei: str | None = None
	external_group: str | None = None
	timezone: str | None = None
	position: dict[str, Any] | None = None
	raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class ProviderUser:
	external_user_id: str
	username: str
	creator_id: str | None = None
	creator_username: str | None = None
	account_id: str | None = None
	account_name: str | None = None
	email: str | None = None
	last_login: int | None = None
	user_flags: int | None = None
	access_rights: int | None = None
	measurement_system: int | None = None
	guid: str | None = None
	host_mask: str | None = None
	two_factor_type: int | None = None
	two_factor_phone: str | None = None
	custom_fields: dict[str, Any] | None = None
	admin_fields: dict[str, Any] | None = None
	raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class ProviderAccount:
	external_account_id: str
	account_name: str
	creator_id: str | None = None
	parent_account_id: str | None = None
	emails: str | None = None
	phones: str | None = None
	guid: str | None = None
	access_rights: int | None = None
	custom_fields: dict[str, Any] | None = None
	admin_fields: dict[str, Any] | None = None
	raw: dict[str, Any] | None = None


class BaseTelematicsProvider:
	def __init__(self, provider_account):
		self.provider_account = provider_account

	def check_connection(self) -> bool:
		raise NotImplementedError

	def list_units(self) -> list[ProviderUnit]:
		raise NotImplementedError

	def list_users(self) -> list[ProviderUser]:
		return []

	def list_accounts(self) -> list[ProviderAccount]:
		return []

	def get_latest_position(self, external_unit_id: str) -> dict[str, Any]:
		raise NotImplementedError
