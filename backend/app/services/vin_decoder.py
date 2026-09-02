"""VIN decoding helpers with graceful fallback behavior."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

VPIC_URL_TEMPLATE = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"

YEAR_CODE_MAP = {
    "A": 2010,
    "B": 2011,
    "C": 2012,
    "D": 2013,
    "E": 2014,
    "F": 2015,
    "G": 2016,
    "H": 2017,
    "J": 2018,
    "K": 2019,
    "L": 2020,
    "M": 2021,
    "N": 2022,
    "P": 2023,
    "R": 2024,
    "S": 2025,
    "T": 2026,
    "V": 2027,
    "W": 2028,
    "X": 2029,
    "Y": 2030,
    "1": 2001,
    "2": 2002,
    "3": 2003,
    "4": 2004,
    "5": 2005,
    "6": 2006,
    "7": 2007,
    "8": 2008,
    "9": 2009,
}


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"0", "Not Applicable", "null", "None"}:
        return None
    return text


def _infer_asset_type(vehicle_type: str | None, body_class: str | None) -> str | None:
    haystack = " ".join(part for part in [vehicle_type or "", body_class or ""] if part).lower()
    if not haystack:
        return None
    if "trailer" in haystack:
        return "trailer"
    if "bus" in haystack:
        return "bus"
    if "tractor" in haystack:
        return "tractor"
    if "excavat" in haystack:
        return "excavator"
    if "hatchback" in haystack:
        return "hatchback"
    if "sedan" in haystack or "saloon" in haystack:
        return "sedan"
    if "truck" in haystack or "pickup" in haystack or "van" in haystack:
        return "truck"
    return "other"


def _fallback_decode(vin: str) -> dict[str, Any]:
    warnings: list[str] = []
    year = YEAR_CODE_MAP.get(vin[9], None) if len(vin) >= 10 else None
    if not year:
        warnings.append("Model year could not be inferred from the VIN pattern.")
    return {
        "success": bool(year),
        "provider": "local_fallback",
        "warnings": warnings or ["External VIN provider unavailable. Limited decode only."],
        "decoded": {
            "vin": vin,
            "normalized_vin": vin,
            "make": None,
            "model": None,
            "year": str(year) if year else None,
            "vehicle_type": None,
            "body_class": None,
            "fuel_type": None,
            "engine_capacity": None,
            "suggested_asset_type": None,
            "manufacturer": None,
        },
    }


async def decode_vin(vin: str) -> dict[str, Any]:
    normalized_vin = "".join(ch for ch in (vin or "").upper().strip() if ch.isalnum())
    if len(normalized_vin) != 17:
        return {
            "success": False,
            "provider": "validation",
            "warnings": ["VIN must be exactly 17 alphanumeric characters."],
            "decoded": {
                "vin": vin,
                "normalized_vin": normalized_vin,
                "make": None,
                "model": None,
                "year": None,
                "vehicle_type": None,
                "body_class": None,
                "fuel_type": None,
                "engine_capacity": None,
                "suggested_asset_type": None,
                "manufacturer": None,
            },
        }

    try:
        async with httpx.AsyncClient(timeout=settings.vin_decode_timeout_seconds) as client:
            response = await client.get(VPIC_URL_TEMPLATE.format(vin=normalized_vin))
            response.raise_for_status()
            payload = response.json()
            row = (payload.get("Results") or [{}])[0]

        vehicle_type = _clean(row.get("VehicleType"))
        body_class = _clean(row.get("BodyClass"))
        displacement_l = _clean(row.get("DisplacementL"))
        engine_capacity = f"{displacement_l} L" if displacement_l else _clean(row.get("EngineModel"))
        decoded = {
            "vin": vin,
            "normalized_vin": normalized_vin,
            "make": _clean(row.get("Make")),
            "model": _clean(row.get("Model")),
            "year": _clean(row.get("ModelYear")),
            "vehicle_type": vehicle_type,
            "body_class": body_class,
            "fuel_type": _clean(row.get("FuelTypePrimary")),
            "engine_capacity": engine_capacity,
            "suggested_asset_type": _infer_asset_type(vehicle_type, body_class),
            "manufacturer": _clean(row.get("Manufacturer")),
        }
        warnings: list[str] = []
        if _clean(row.get("ErrorCode")) not in {None, "0"}:
            warning_text = _clean(row.get("ErrorText"))
            if warning_text:
                warnings.append(warning_text)
        if not any(decoded.get(field) for field in ["make", "model", "year", "vehicle_type", "body_class"]):
            warnings.append("VIN provider returned limited metadata for this asset.")
        return {
            "success": any(decoded.get(field) for field in ["make", "model", "year", "vehicle_type", "body_class"]),
            "provider": "nhtsa_vpic",
            "warnings": warnings,
            "decoded": decoded,
        }
    except Exception:
        return _fallback_decode(normalized_vin)
