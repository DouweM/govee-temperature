"""Data models for Govee API - Home Assistant compatible version."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from dataclasses import field
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceSettings:
    """Device settings from deviceSettings JSON."""

    device_type: int | None = None
    push_state: bool | None = None
    tem_min: int | None = None
    tem_max: int | None = None
    tem_warning: bool | None = None
    tem_cali: int | None = None
    hum_min: int | None = None
    hum_max: int | None = None
    hum_warning: bool | None = None
    hum_cali: int | None = None
    battery: int | None = None
    wifi_level: int | None = None
    upload_rate: int | None = None
    power_save_mode_state: bool | None = None
    fah_open: bool | None = None
    net_waring: bool | None = None  # Note: API typo
    device_name: str | None = None
    sku: str | None = None
    device: str | None = None
    version_hard: str | None = None
    version_soft: str | None = None
    gateway_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceSettings:
        """Create from API data dict."""
        return cls(
            device_type=data.get("deviceType"),
            push_state=data.get("pushState"),
            tem_min=data.get("temMin"),
            tem_max=data.get("temMax"),
            tem_warning=data.get("temWarning"),
            tem_cali=data.get("temCali"),
            hum_min=data.get("humMin"),
            hum_max=data.get("humMax"),
            hum_warning=data.get("humWarning"),
            hum_cali=data.get("humCali"),
            battery=data.get("battery"),
            wifi_level=data.get("wifiLevel"),
            upload_rate=data.get("uploadRate"),
            power_save_mode_state=data.get("powerSaveModeState"),
            fah_open=data.get("fahOpen"),
            net_waring=data.get("netWaring"),
            device_name=data.get("deviceName"),
            sku=data.get("sku"),
            device=data.get("device"),
            version_hard=data.get("versionHard"),
            version_soft=data.get("versionSoft"),
            gateway_id=data.get("gatewayId"),
        )


@dataclass
class LastDeviceData:
    """Last device data from lastDeviceData JSON."""

    online: bool | None = None
    tem: int | None = None  # Temperature in hundredths (2160 = 21.6°C)
    hum: int | None = None  # Humidity in hundredths (5500 = 55.0%)
    last_time: int | None = None
    avg_day_tem: int | None = None
    avg_day_hum: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LastDeviceData:
        """Create from API data dict."""
        return cls(
            online=data.get("online"),
            tem=cls._validate_sensor_value(data.get("tem")),
            hum=cls._validate_sensor_value(data.get("hum")),
            last_time=data.get("lastTime"),
            avg_day_tem=cls._validate_sensor_value(data.get("avgDayTem")),
            avg_day_hum=cls._validate_sensor_value(data.get("avgDayHum")),
        )

    @staticmethod
    def _validate_sensor_value(v: Any) -> int | None:
        """Validate sensor values, treating None and 0 as distinct."""
        if v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None


@dataclass
class DeviceExt:
    """Device extension data."""

    device_settings: str | None = None
    last_device_data: str | None = None
    device_splice: str | None = None
    ext_resources: str | None = None
    shared_settings: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceExt:
        """Create from API data dict."""
        return cls(
            device_settings=data.get("deviceSettings"),
            last_device_data=data.get("lastDeviceData"),
            device_splice=data.get("deviceSplice"),
            ext_resources=data.get("extResources"),
            shared_settings=data.get("sharedSettings"),
        )

    def get_parsed_device_settings(self) -> DeviceSettings | None:
        """Parse device settings JSON."""
        if not self.device_settings:
            return None
        try:
            data = json.loads(self.device_settings)
            return DeviceSettings.from_dict(data)
        except (json.JSONDecodeError, ValueError):
            return None

    def get_parsed_last_device_data(self) -> LastDeviceData | None:
        """Parse last device data JSON."""
        if not self.last_device_data:
            return None
        try:
            data = json.loads(self.last_device_data)
            return LastDeviceData.from_dict(data)
        except (json.JSONDecodeError, ValueError):
            return None


@dataclass
class DeviceData:
    """Processed device sensor data."""

    temperature: float | None = None
    humidity: float | None = None
    battery: int | None = None
    online: bool | None = None
    wifi_level: int | None = None
    temperature_warning: bool | None = None
    humidity_warning: bool | None = None
    upload_rate: int | None = None
    power_save_mode: bool | None = None
    last_seen: int | None = None
    avg_day_temperature: float | None = None
    avg_day_humidity: float | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class GoveeDevice:
    """Govee device information."""

    device_id: int
    group_id: int
    sku: str
    device: str  # MAC address
    version_hard: str
    version_soft: str
    device_name: str
    device_ext: DeviceExt
    name: str = field(init=False)
    mac: str = field(init=False)
    model: str = field(init=False)
    data: DeviceData = field(init=False)

    def __post_init__(self) -> None:
        """Set computed fields after initialization."""
        self.name = self.device_name
        self.mac = self.device
        self.model = self.sku

        # Parse device settings and last device data
        device_settings = self.device_ext.get_parsed_device_settings()
        last_device_data = self.device_ext.get_parsed_last_device_data()

        # Build comprehensive device data
        self.data = DeviceData(
            temperature=self._convert_temperature(last_device_data.tem if last_device_data else None),
            humidity=self._convert_humidity(last_device_data.hum if last_device_data else None),
            battery=device_settings.battery if device_settings else None,
            online=last_device_data.online if last_device_data else None,
            wifi_level=device_settings.wifi_level if device_settings else None,
            temperature_warning=device_settings.tem_warning if device_settings else None,
            humidity_warning=device_settings.hum_warning if device_settings else None,
            upload_rate=device_settings.upload_rate if device_settings else None,
            power_save_mode=device_settings.power_save_mode_state if device_settings else None,
            last_seen=last_device_data.last_time if last_device_data else None,
            avg_day_temperature=self._convert_temperature(last_device_data.avg_day_tem if last_device_data else None),
            avg_day_humidity=self._convert_humidity(last_device_data.avg_day_hum if last_device_data else None),
            raw_data={
                "device_settings": device_settings.__dict__ if device_settings else None,
                "last_device_data": last_device_data.__dict__ if last_device_data else None,
            }
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoveeDevice:
        """Create from API data dict."""
        return cls(
            device_id=data["deviceId"],
            group_id=data["groupId"],
            sku=data["sku"],
            device=data["device"],
            version_hard=data["versionHard"],
            version_soft=data["versionSoft"],
            device_name=data["deviceName"],
            device_ext=DeviceExt.from_dict(data["deviceExt"]),
        )

    @staticmethod
    def _convert_temperature(temp_hundredths: int | None) -> float | None:
        """Convert temperature from hundredths to Celsius."""
        if temp_hundredths is None:
            return None
        return temp_hundredths / 100.0

    @staticmethod
    def _convert_humidity(hum_hundredths: int | None) -> float | None:
        """Convert humidity from hundredths to percentage."""
        if hum_hundredths is None:
            return None
        return hum_hundredths / 100.0

    @classmethod
    def from_api_response(cls, device: dict[str, Any]) -> GoveeDevice | None:
        """Create GoveeDevice from API response data."""
        try:
            return cls.from_dict(device)
        except (ValueError, KeyError) as e:
            _LOGGER.warning("Failed to parse device: %s", e)
            return None
