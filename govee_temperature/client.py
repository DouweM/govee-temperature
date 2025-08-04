"""Govee API client."""

from __future__ import annotations

import httpx

from .models import GoveeDevice


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
        """Initialize the Govee client.

        Args:
            auth_token: Bearer token for authentication
            client_id: Client ID for API requests
            api_url: API endpoint URL (optional)
            user_agent: User agent string (optional)
            app_version: App version string (optional)
            timeout: Request timeout in seconds
        """
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
        """Fetch all temperature/humidity devices from the API.

        Returns:
            List of GoveeDevice objects with temperature data

        Raises:
            GoveeAuthenticationError: If authentication fails
            GoveeConnectionError: If connection fails
            GoveeClientError: For other API errors
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url, headers=self._headers)

                if response.status_code == 401:
                    raise GoveeAuthenticationError("Authentication failed")

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
                raise GoveeAuthenticationError("Authentication failed") from err
            raise GoveeClientError(f"HTTP error: {err.response.status_code}") from err
        except httpx.RequestError as err:
            raise GoveeConnectionError(f"Connection error: {err}") from err
        except Exception as err:
            raise GoveeClientError(f"Unexpected error: {err}") from err

    async def get_device_by_name(self, device_name: str) -> GoveeDevice | None:
        """Get a specific device by name.

        Args:
            device_name: Name of the device to find

        Returns:
            GoveeDevice if found, None otherwise
        """
        devices = await self.get_devices()
        return next((device for device in devices if device.name == device_name), None)

    async def get_temperature(self, device_name: str) -> float | None:
        """Get temperature for a specific device by name.

        Args:
            device_name: Name of the device

        Returns:
            Temperature in Celsius, or None if device not found or no temperature data
        """
        device = await self.get_device_by_name(device_name)
        return device.data.temperature if device else None
