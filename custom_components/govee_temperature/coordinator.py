"""DataUpdateCoordinator for Govee Temperature."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .client import GoveeAuthenticationError
from .client import GoveeClient
from .client import GoveeConnectionError
from .const import CONF_AUTH_TOKEN
from .const import CONF_CLIENT_ID
from .const import DEFAULT_SCAN_INTERVAL
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GoveeTemperatureCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Govee temperature data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.client = GoveeClient(
            auth_token=entry.data[CONF_AUTH_TOKEN],
            client_id=entry.data[CONF_CLIENT_ID],
        )

        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Govee API."""
        try:
            devices = await self.client.get_devices()

            # Convert to format expected by Home Assistant sensors
            processed_devices: dict[str, dict[str, Any]] = {}
            for device in devices:
                processed_devices[device.mac] = {
                    "name": device.name,
                    "mac": device.mac,
                    "temperature": device.data.temperature,
                    "humidity": device.data.humidity,
                    "battery": device.data.battery,
                    "online": device.data.online,
                    "wifi_level": device.data.wifi_level,
                    "temperature_warning": device.data.temperature_warning,
                    "humidity_warning": device.data.humidity_warning,
                    "upload_rate": device.data.upload_rate,
                    "power_save_mode": device.data.power_save_mode,
                    "last_seen": device.data.last_seen,
                    "avg_day_temperature": device.data.avg_day_temperature,
                    "avg_day_humidity": device.data.avg_day_humidity,
                    "model": device.model,
                    "raw_data": device.data.raw_data,
                }

            _LOGGER.debug("Processed %d temperature devices", len(processed_devices))
            return processed_devices

        except GoveeAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GoveeConnectionError as err:
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
