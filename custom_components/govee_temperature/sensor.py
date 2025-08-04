"""Sensor platform for Govee Temperature integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.const import EntityCategory
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_MODELS
from .const import DOMAIN
from .coordinator import GoveeTemperatureCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "temperature": SensorEntityDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    "humidity": SensorEntityDescription(
        key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    "battery": SensorEntityDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "online": SensorEntityDescription(
        key="online",
        name="Online Status",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "wifi_level": SensorEntityDescription(
        key="wifi_level",
        name="WiFi Signal Level",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "temperature_warning": SensorEntityDescription(
        key="temperature_warning",
        name="Temperature Warning",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "humidity_warning": SensorEntityDescription(
        key="humidity_warning",
        name="Humidity Warning",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "upload_rate": SensorEntityDescription(
        key="upload_rate",
        name="Upload Rate",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="s",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "power_save_mode": SensorEntityDescription(
        key="power_save_mode",
        name="Power Save Mode",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "avg_day_temperature": SensorEntityDescription(
        key="avg_day_temperature",
        name="Average Daily Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "avg_day_humidity": SensorEntityDescription(
        key="avg_day_humidity",
        name="Average Daily Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee Temperature sensors from a config entry."""
    coordinator: GoveeTemperatureCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for device_mac, device_data in coordinator.data.items():
        device_name = device_data["name"]

        # Add sensors based on available data, with special handling for edge cases
        for sensor_type, description in SENSOR_DESCRIPTIONS.items():
            sensor_value = device_data.get(sensor_type)

            # Include sensor if:
            # 1. Value is not None (but allow False, 0, 0.0 for valid states)
            # 2. For humidity, include even if 0.0% (valid state for some sensors)
            # 3. For boolean sensors, include if explicitly set
            if (
                sensor_value is not None or
                (sensor_type == "humidity" and sensor_value == 0.0) or
                (sensor_type in ["online", "temperature_warning", "humidity_warning", "power_save_mode"] and sensor_value is not None)
            ):
                entities.append(GoveeSensor(coordinator, device_mac, device_name, description))

    async_add_entities(entities)


class GoveeSensor(CoordinatorEntity[GoveeTemperatureCoordinator], SensorEntity):
    """Govee sensor entity."""

    def __init__(
        self,
        coordinator: GoveeTemperatureCoordinator,
        device_mac: str,
        device_name: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_mac = device_mac
        self._device_name = device_name
        self._attr_unique_id = f"{device_mac}_{description.key}"
        self._attr_name = f"{device_name} {description.key.title()}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_data = self.coordinator.data.get(self._device_mac, {})
        model = self._get_device_model(device_data)

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_mac)},
            name=self._device_name,
            manufacturer="Govee",
            model=model,
            hw_version=self._device_mac,
        )

    def _get_device_model(self, device_data: dict) -> str:
        """Determine device model based on SKU or available sensors."""
        # Use SKU from device data if available
        model_sku = device_data.get("model", "Unknown")
        if model_sku in DEVICE_MODELS:
            return DEVICE_MODELS[model_sku]
        elif model_sku != "Unknown":
            return f"{model_sku} Sensor"

        # Fallback to sensor-based detection
        has_temp = device_data.get("temperature") is not None
        has_humidity = device_data.get("humidity") is not None

        if has_temp and has_humidity:
            return "Temperature/Humidity Sensor"
        elif has_temp:
            return "Temperature Sensor"
        elif has_humidity:
            return "Humidity Sensor"
        else:
            return "Sensor"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success or self._device_mac not in self.coordinator.data:
            return False

        device_data = self.coordinator.data[self._device_mac]
        sensor_value = device_data.get(self.entity_description.key)

        # Special handling for different sensor types
        if self.entity_description.key == "humidity":
            # Humidity sensor is available even if reading is 0.0%
            return sensor_value is not None
        elif self.entity_description.key in ["online", "temperature_warning", "humidity_warning", "power_save_mode"]:
            # Boolean sensors are available if explicitly set (including False)
            return sensor_value is not None
        else:
            # Standard sensors require non-None values
            return sensor_value is not None

    @property
    def native_value(self) -> float | int | bool | str | None:
        """Return the sensor value."""
        if self._device_mac not in self.coordinator.data:
            return None

        sensor_value = self.coordinator.data[self._device_mac].get(self.entity_description.key)

        # Handle boolean sensors that should show as On/Off
        if self.entity_description.key in ["online", "temperature_warning", "humidity_warning", "power_save_mode"]:
            if sensor_value is None:
                return None
            return "On" if sensor_value else "Off"

        return sensor_value
