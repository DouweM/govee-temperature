"""Data models for Govee API."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class DeviceSettings(BaseModel):
    """Device settings from deviceSettings JSON."""

    device_type: int | None = Field(None, alias="deviceType")
    push_state: bool | None = Field(None, alias="pushState")
    tem_min: int | None = Field(None, alias="temMin")
    tem_max: int | None = Field(None, alias="temMax")
    tem_warning: bool | None = Field(None, alias="temWarning")
    tem_cali: int | None = Field(None, alias="temCali")
    hum_min: int | None = Field(None, alias="humMin")
    hum_max: int | None = Field(None, alias="humMax")
    hum_warning: bool | None = Field(None, alias="humWarning")
    hum_cali: int | None = Field(None, alias="humCali")
    battery: int | None = None
    wifi_level: int | None = Field(None, alias="wifiLevel")
    upload_rate: int | None = Field(None, alias="uploadRate")
    power_save_mode_state: bool | None = Field(None, alias="powerSaveModeState")
    fah_open: bool | None = Field(None, alias="fahOpen")
    net_waring: bool | None = Field(None, alias="netWaring")  # Note: API typo
    device_name: str | None = Field(None, alias="deviceName")
    sku: str | None = None
    device: str | None = None
    version_hard: str | None = Field(None, alias="versionHard")
    version_soft: str | None = Field(None, alias="versionSoft")
    gateway_id: int | None = Field(None, alias="gatewayId")


class LastDeviceData(BaseModel):
    """Last device data from lastDeviceData JSON."""

    online: bool | None = None
    tem: int | None = None  # Temperature in hundredths (2160 = 21.6°C)
    hum: int | None = None  # Humidity in hundredths (5500 = 55.0%)
    last_time: int | None = Field(None, alias="lastTime")
    avg_day_tem: int | None = Field(None, alias="avgDayTem")
    avg_day_hum: int | None = Field(None, alias="avgDayHum")

    @field_validator("tem", "hum", "avg_day_tem", "avg_day_hum", mode="before")
    @classmethod
    def validate_sensor_values(cls, v):
        """Validate sensor values, treating None and 0 as distinct."""
        if v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None


class DeviceExt(BaseModel):
    """Device extension data."""

    device_settings: str | None = Field(None, alias="deviceSettings")
    last_device_data: str | None = Field(None, alias="lastDeviceData")
    device_splice: str | None = Field(None, alias="deviceSplice")
    ext_resources: str | None = Field(None, alias="extResources")
    shared_settings: str | None = Field(None, alias="sharedSettings")

    def get_parsed_device_settings(self) -> DeviceSettings | None:
        """Parse device settings JSON."""
        if not self.device_settings:
            return None
        try:
            data = json.loads(self.device_settings)
            return DeviceSettings.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None

    def get_parsed_last_device_data(self) -> LastDeviceData | None:
        """Parse last device data JSON."""
        if not self.last_device_data:
            return None
        try:
            data = json.loads(self.last_device_data)
            return LastDeviceData.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None


class DeviceData(BaseModel):
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
    raw_data: dict[str, Any] | None = None


class GoveeDevice(BaseModel):
    """Govee device information."""

    device_id: int = Field(alias="deviceId")
    group_id: int = Field(alias="groupId")
    sku: str
    device: str  # MAC address
    version_hard: str = Field(alias="versionHard")
    version_soft: str = Field(alias="versionSoft")
    device_name: str = Field(alias="deviceName")
    device_ext: DeviceExt = Field(alias="deviceExt")

    name: str = Field(default="")
    mac: str = Field(default="")
    model: str = Field(default="")
    data: DeviceData = Field(default_factory=lambda: DeviceData())

    @model_validator(mode="after")
    def set_computed_fields(self):
        """Set computed fields after validation."""
        self.name = self.device_name
        self.mac = self.device
        self.model = self.sku

        # Parse device settings and last device data
        device_settings = self.device_ext.get_parsed_device_settings()
        last_device_data = self.device_ext.get_parsed_last_device_data()

        # Build comprehensive device data
        self.data = DeviceData(
            temperature=self._convert_temperature(
                last_device_data.tem if last_device_data else None
            ),
            humidity=self._convert_humidity(last_device_data.hum if last_device_data else None),
            battery=device_settings.battery if device_settings else None,
            online=last_device_data.online if last_device_data else None,
            wifi_level=device_settings.wifi_level if device_settings else None,
            temperature_warning=device_settings.tem_warning if device_settings else None,
            humidity_warning=device_settings.hum_warning if device_settings else None,
            upload_rate=device_settings.upload_rate if device_settings else None,
            power_save_mode=device_settings.power_save_mode_state if device_settings else None,
            last_seen=last_device_data.last_time if last_device_data else None,
            avg_day_temperature=self._convert_temperature(
                last_device_data.avg_day_tem if last_device_data else None
            ),
            avg_day_humidity=self._convert_humidity(
                last_device_data.avg_day_hum if last_device_data else None
            ),
            raw_data={
                "device_settings": device_settings.model_dump() if device_settings else None,
                "last_device_data": last_device_data.model_dump() if last_device_data else None,
            },
        )

        return self

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
            return cls.model_validate(device)
        except ValueError as e:
            print(f"Failed to parse device: {e}")
            return None
