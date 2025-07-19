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
GOVEE_DEVICE_NAME=your_device_name
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

Build and run:
```bash
docker build -t govee-temperature .
docker run -p 8000:8000 --env-file .env govee-temperature
```