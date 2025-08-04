"""Govee API client for Home Assistant integration."""

from __future__ import annotations

import httpx
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from govee_temperature.models import GoveeDevice


class GoveeClientError(Exception):
    """Base exception for Govee client errors."""


class GoveeAuthenticationError(GoveeClientError):
    """Authentication error."""


class GoveeConnectionError(GoveeClientError):
    """Connection error."""


class GoveeClient:
    """Client for interacting with Govee API."""

    DEFAULT_API_URL = "https://app2.govee.com/bff-app/v1/device/list"
    DEFAULT_USER_AGENT = (
        "GoveeHome/7.0.12 (com.ihoment.GoVeeSensor; build:3; iOS 18.5.0) Alamofire/5.6.4"
    )
    DEFAULT_APP_VERSION = "7.0.12"
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        auth_token: str,
        client_id: str,
        api_url: str | None = None,
        user_agent: str | None = None,
        app_version: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the Govee client."""
        self.auth_token = auth_token
        self.client_id = client_id
        self.api_url = api_url or self.DEFAULT_API_URL
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.app_version = app_version or self.DEFAULT_APP_VERSION
        self.timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "clientId": self.client_id,
            "User-Agent": self.user_agent,
            "appVersion": self.app_version,
        }

    async def get_devices(self) -> list[GoveeDevice]:
        """Fetch all temperature/humidity devices from the API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url, headers=self._headers)

                if response.status_code == 401:
                    raise ConfigEntryAuthFailed("Authentication failed")

                response.raise_for_status()
                data = response.json()

                devices = []
                for device_data in data.get("data", {}).get("devices", []):
                    device = GoveeDevice.from_api_response(device_data)
                    if device:
                        devices.append(device)

                return devices

        except httpx.HTTPStatusError as err:
            if err.response.status_code == 401:
                raise ConfigEntryAuthFailed("Authentication failed") from err
            raise UpdateFailed(f"HTTP error: {err.response.status_code}") from err
        except httpx.RequestError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
