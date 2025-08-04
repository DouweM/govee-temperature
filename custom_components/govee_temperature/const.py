"""Constants for the Govee Temperature integration."""

from typing import Final

DOMAIN: Final = "govee_temperature"

CONF_AUTH_TOKEN: Final = "auth_token"
CONF_CLIENT_ID: Final = "client_id"

DEFAULT_SCAN_INTERVAL: Final = 300  # 5 minutes
DEFAULT_TIMEOUT: Final = 30
MIN_SCAN_INTERVAL: Final = 60  # 1 minute minimum to avoid rate limiting

GOVEE_API_URL: Final = "https://app2.govee.com/bff-app/v1/device/list"
DEFAULT_USER_AGENT: Final = (
    "GoveeHome/7.0.12 (com.ihoment.GoVeeSensor; build:3; iOS 18.5.0) Alamofire/5.6.4"
)
DEFAULT_APP_VERSION: Final = "7.0.12"

# Known device models
DEVICE_MODELS: Final = {
    "H5051": "WiFi Thermo-Hygrometer",
    "H5074": "Bluetooth Thermo-Hygrometer",
    "H5075": "Bluetooth Thermo-Hygrometer",
    "H5101": "WiFi Thermo-Hygrometer",
    "H5102": "WiFi Thermo-Hygrometer",
    "H5179": "WiFi Thermo-Hygrometer",
}
