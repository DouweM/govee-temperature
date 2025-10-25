"""
Govee API temperature fetcher web service.
Provides HTTP endpoints for fetching temperature data from Govee devices.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException

from .client import GoveeAuthenticationError
from .client import GoveeClient
from .client import GoveeClientError
from .client import GoveeConnectionError

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Govee Temperature API",
    description="HTTP API for fetching temperature data from Govee devices",
    version="1.0.0",
)


def _get_client() -> GoveeClient:
    """Create Govee client from environment variables."""
    auth_token = os.getenv("GOVEE_AUTH_TOKEN")
    client_id = os.getenv("GOVEE_CLIENT_ID")

    if not auth_token or not client_id:
        raise HTTPException(
            status_code=500,
            detail="Missing required environment variables: GOVEE_AUTH_TOKEN, GOVEE_CLIENT_ID",
        )

    return GoveeClient(auth_token=auth_token, client_id=client_id)


@app.get("/devices")
async def get_devices():
    """Get all available Govee devices with temperature sensors.

    Returns:
        JSON response with list of devices that have temperature data
    """
    try:
        client = _get_client()
        devices = await client.get_devices()

        return {
            "devices": [
                {
                    "name": device.name,
                    "mac": device.mac,
                    "model": device.model,
                    "temperature": device.data.temperature,
                    "humidity": device.data.humidity,
                    "battery": device.data.battery,
                }
                for device in devices
            ]
        }

    except GoveeAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except GoveeConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except GoveeClientError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/device/{device_name}")
async def get_device(device_name: str):
    """Get sensor data for a specific device by name.

    Args:
        device_name: Name of the Govee device

    Returns:
        JSON response with device information and sensor data
    """
    try:
        client = _get_client()
        device = await client.get_device_by_name(device_name)

        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_name}' not found")

        return {
            "name": device.name,
            "mac": device.mac,
            "model": device.model,
            "temperature": device.data.temperature,
            "humidity": device.data.humidity,
            "battery": device.data.battery,
        }

    except GoveeAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except GoveeConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except GoveeClientError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
