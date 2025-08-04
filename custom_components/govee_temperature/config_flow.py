"""Config flow for Govee Temperature integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .client import GoveeClient
from .const import CONF_AUTH_TOKEN
from .const import CONF_CLIENT_ID
from .const import DEFAULT_SCAN_INTERVAL
from .const import DOMAIN
from .const import MIN_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AUTH_TOKEN): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    try:
        client = GoveeClient(
            auth_token=data[CONF_AUTH_TOKEN],
            client_id=data[CONF_CLIENT_ID],
        )

        devices = await client.get_devices()

        if not devices:
            raise CannotConnect("No temperature devices found in Govee account")

        device_names = [device.name for device in devices]
        _LOGGER.info("Found %d temperature devices: %s", len(devices), device_names)

        return {"title": f"Govee Temperature ({len(devices)} devices)"}

    except Exception as err:
        # The client raises HA exceptions directly
        if "Authentication failed" in str(err):
            raise InvalidAuth from err
        else:
            raise CannotConnect from err


class GoveeTemperatureConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Govee Temperature."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(f"govee_temperature_{user_input[CONF_CLIENT_ID]}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
