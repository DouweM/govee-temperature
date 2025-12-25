"""Config flow for Govee Temperature integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
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


STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AUTH_TOKEN): str,
    }
)


class GoveeTemperatureConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Govee Temperature."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthorization request."""
        entry_id = self.context.get("entry_id")
        if entry_id:
            self._reauth_entry = self.hass.config_entries.async_get_entry(entry_id)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthorization confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            assert self._reauth_entry is not None
            # Combine new auth token with existing client_id for validation
            validation_data = {
                CONF_AUTH_TOKEN: user_input[CONF_AUTH_TOKEN],
                CONF_CLIENT_ID: self._reauth_entry.data[CONF_CLIENT_ID],
            }

            try:
                await validate_input(self.hass, validation_data)

                # Update the config entry with new auth token
                new_data = {**self._reauth_entry.data, **user_input}
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry, data=new_data
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
        )

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
