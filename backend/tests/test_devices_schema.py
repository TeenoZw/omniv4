"""Tests for device schema serialization."""
from datetime import datetime, timezone

from app.models.hardware import HardwareStatus
from app.schemas.devices import DeviceInventoryUpdateRequest


def test_device_inventory_update_request_serializes_extended_fields():
    """Ensure extended optional fields remain available after serialization."""

    payload = DeviceInventoryUpdateRequest(
        status=HardwareStatus.ACTIVE,
        firmware_version="2.5.1",
        hardware_type="satellite",
        model="OmniTrack Ultra",
        manufacturer="Omni Advanced",
        serial_number="SN-TEST-9001",
        purchase_date=datetime(2025, 12, 10, 12, 0, 0, tzinfo=timezone.utc),
        notes="Integration test payload",
    )

    serialized = payload.model_dump(exclude_none=True)

    assert serialized["status"] == HardwareStatus.ACTIVE
    assert serialized["firmware_version"] == "2.5.1"
    assert serialized["hardware_type"] == "satellite"
    assert serialized["model"] == "OmniTrack Ultra"
    assert serialized["manufacturer"] == "Omni Advanced"
    assert serialized["serial_number"] == "SN-TEST-9001"
    assert serialized["notes"] == "Integration test payload"
    assert serialized["purchase_date"] == datetime(2025, 12, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Ensure purchase_date stays timezone-aware to avoid downstream stripping
    assert serialized["purchase_date"].tzinfo is not None

    # `model_fields_set` should reflect every explicitly provided field for route logic
    assert payload.model_fields_set.issuperset(
        {
            "status",
            "firmware_version",
            "hardware_type",
            "model",
            "manufacturer",
            "serial_number",
            "notes",
            "purchase_date",
        }
    )
