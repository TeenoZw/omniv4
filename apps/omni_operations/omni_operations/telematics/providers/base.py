from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderUnit:
	external_unit_id: str
	external_unit_name: str | None = None
	external_device_id: str | None = None
	external_imei: str | None = None
	external_group: str | None = None
	timezone: str | None = None
	position: dict[str, Any] | None = None
	raw: dict[str, Any] | None = None


class BaseTelematicsProvider:
	def __init__(self, provider_account):
		self.provider_account = provider_account

	def check_connection(self) -> bool:
		raise NotImplementedError

	def list_units(self) -> list[ProviderUnit]:
		raise NotImplementedError

	def get_latest_position(self, external_unit_id: str) -> dict[str, Any]:
		raise NotImplementedError
