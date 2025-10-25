"""Binary sensor platform for Govee Temperature integration."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_MODELS
from .const import DOMAIN
from .coordinator import GoveeTemperatureCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS: dict[str, BinarySensorEntityDescription] = {
    "online": BinarySensorEntityDescription(
        key="online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "temperature_warning": BinarySensorEntityDescription(
        key="temperature_warning",
        name="Temperature Warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "humidity_warning": BinarySensorEntityDescription(
        key="humidity_warning",
        name="Humidity Warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "power_save_mode": BinarySensorEntityDescription(
        key="power_save_mode",
        name="Power Save Mode",
        device_class=BinarySensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Govee Temperature binary sensors from a config entry."""
    coordinator: GoveeTemperatureCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    for device_mac, device_data in coordinator.data.items():
        device_name = device_data["name"]

        # Add binary sensors based on available data
        for sensor_type, description in BINARY_SENSOR_DESCRIPTIONS.items():
            sensor_value = device_data.get(sensor_type)

            # Include binary sensor if value is not None
            # This allows False as a valid state
            if sensor_value is not None:
                entities.append(
                    GoveeBinarySensor(coordinator, device_mac, device_name, description)
                )

    async_add_entities(entities)


class GoveeBinarySensor(CoordinatorEntity[GoveeTemperatureCoordinator], BinarySensorEntity):
    """Govee binary sensor entity."""

    def __init__(
        self,
        coordinator: GoveeTemperatureCoordinator,
        device_mac: str,
        device_name: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_mac = device_mac
        self._device_name = device_name
        self._attr_unique_id = f"{device_mac}_{description.key}"
        # Use the description name if provided, otherwise title case the key
        display_name = description.name if description.name else description.key.replace("_", " ").title()
        self._attr_name = f"{device_name} {display_name}"

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
        if (
            not self.coordinator.last_update_success
            or self._device_mac not in self.coordinator.data
        ):
            return False

        device_data = self.coordinator.data[self._device_mac]
        sensor_value = device_data.get(self.entity_description.key)

        # Binary sensors are available if explicitly set (including False)
        return sensor_value is not None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self._device_mac not in self.coordinator.data:
            return None

        sensor_value = self.coordinator.data[self._device_mac].get(self.entity_description.key)

        # Return the boolean value directly
        # None means unavailable, False means off, True means on
        return sensor_value
