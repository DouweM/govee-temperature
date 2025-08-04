"""Data models for Govee API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DeviceData:
    """Device sensor data."""

    temperature: float | None = None
    humidity: float | None = None
    battery: int | None = None
    raw_data: dict[str, Any] | None = None


@dataclass
class GoveeDevice:
    """Govee device information."""

    name: str
    mac: str
    model: str
    data: DeviceData

    @classmethod
    def from_api_response(cls, device: dict[str, Any]) -> GoveeDevice | None:
        """Create GoveeDevice from API response data."""
        device_name = device.get("deviceName")
        device_mac = device.get("device")

        if not device_name or not device_mac:
            return None

        device_ext = device.get("deviceExt", {})
        last_device_data_str = device_ext.get("lastDeviceData", "{}")

        try:
            import json

            last_device_data = json.loads(last_device_data_str)

            # Check if device has temperature data
            if "tem" not in last_device_data:
                return None

            temperature = last_device_data.get("tem")
            humidity = last_device_data.get("hum")
            battery = last_device_data.get("battery")

            data = DeviceData(
                temperature=temperature / 100.0 if temperature is not None else None,
                humidity=humidity / 100.0 if humidity is not None else None,
                battery=battery,
                raw_data=last_device_data,
            )

            return cls(
                name=device_name,
                mac=device_mac,
                model=device.get("sku", "Unknown"),
                data=data,
            )

        except (json.JSONDecodeError, TypeError):
            return None
