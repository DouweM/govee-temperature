# Govee Temperature API

Fetches temperature data from Govee devices using the mobile app API.

Inspired by [govee_h5042_sensor](https://github.com/clong/govee_h5042_sensor).

## Getting Govee Credentials

1. Download [Proxyman](https://proxyman.io/ios) onto your iOS device
2. Configure Proxyman to intercept HTTPS connections for `app2.govee.com` (More -> SSL Proxying List)
3. Install the Proxyman profile and certificate according to the app's instructions
4. While Proxyman VPN is active, open your Govee app and check your temperature sensor
5. In Proxyman, find the request to `https://app2.govee.com/device/rest/devices/v1/list`
6. Copy the `Authorization` header value (Bearer token) and `clientId` header value

## Setup

1. Create `.env` file with your Govee credentials:
```
GOVEE_AUTH_TOKEN=your_bearer_token_from_authorization_header
GOVEE_CLIENT_ID=your_client_id_from_header
GOVEE_DEVICE_NAME=your_device_name_in_govee_app
```

2. Install dependencies:
```bash
uv sync
```

## Usage

Run the API server:
```bash
uv run govee-temperature
```

Get temperature reading:
```bash
curl http://localhost:8000/temperature
```

Example response:
```json
{
  "temperature": 23.45
}
```

## Docker

### Using Pre-built Image

Run using the pre-built image from GitHub Container Registry:
```bash
docker run -p 8000:8000 \
  -e GOVEE_AUTH_TOKEN=your_bearer_token \
  -e GOVEE_CLIENT_ID=your_client_id \
  -e GOVEE_DEVICE_NAME=your_device_name \
  ghcr.io/douwem/govee-temperature:latest
```

Or with an `.env` file:
```bash
docker run -p 8000:8000 --env-file .env ghcr.io/douwem/govee-temperature:latest
```

### Build Locally

Build and run locally:
```bash
docker build -t govee-temperature .
docker run -p 8000:8000 --env-file .env govee-temperature
```

## Home Assistant Integration

Add to your Home Assistant `configuration.yaml`:

```yaml
sensor:
  - platform: rest
    unique_id: jacuzzi-temperature
    name: "Jacuzzi Temperature"
    resource: "http://localhost:8000/temperature"
    scan_interval: 120
    device_class: temperature
    unit_of_measurement: "°C"
    value_template: "{{ value_json.temperature }}"
```

Replace the URL with your deployed API endpoint and adjust the sensor name/unique_id as needed.
