# Govee Temperature API

Fetches temperature data from Govee devices using the mobile app API.

Inspired by [govee_h5042_sensor](https://github.com/clong/govee_h5042_sensor).

## Setup

1. Create `.env` file with your Govee credentials:
```
GOVEE_AUTH_TOKEN=your_bearer_token
GOVEE_CLIENT_ID=your_client_id
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