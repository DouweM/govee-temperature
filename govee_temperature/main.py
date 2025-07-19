"""
Govee API temperature fetcher
Fetches temperature data for a specific device from the Govee API
"""

import json
import os
from typing import Optional
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# Load environment variables
load_dotenv()

app = FastAPI(title="Govee Temperature API")


async def fetch_device_temperature(
    auth_token: str,
    client_id: str,
    device_name: str,
    user_agent: str = "GoveeHome/7.0.12 (com.ihoment.GoVeeSensor; build:3; iOS 18.5.0) Alamofire/5.6.4",
    app_version: str = "7.0.12"
) -> Optional[float]:
    """
    Fetch temperature data for a specific device from Govee API.

    Args:
        auth_token: Bearer token for authentication
        client_id: Client ID for the API request
        device_name: Name of the device to search for
        user_agent: User agent string (default: Govee app user agent)
        app_version: App version (default: "7.0.12")

    Returns:
        Temperature value as float (converted from 100ths), or None if device not found or error occurs
    """
    try:
        url = "https://app2.govee.com/bff-app/v1/device/list"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "clientId": client_id,
            "User-Agent": user_agent,
            "appVersion": app_version
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Find the device with matching name
            for device in data.get("data", {}).get("devices", []):
                if device.get("deviceName") == device_name:
                    # Parse the lastDeviceData JSON string
                    device_ext = device.get("deviceExt", {})
                    last_device_data_str = device_ext.get("lastDeviceData", "{}")
                    last_device_data = json.loads(last_device_data_str)

                    # Extract temperature value and convert from 100ths
                    temperature = last_device_data.get("tem")
                    if temperature is not None:
                        return temperature / 100.0
                    return None

            print(f"Device '{device_name}' not found")
            return None

    except Exception as e:
        print(f"Error fetching temperature data: {e}")
        return None


@app.get("/temperature")
async def get_temperature():
    """Get current temperature from Govee device."""
    auth_token = os.getenv("GOVEE_AUTH_TOKEN")
    client_id = os.getenv("GOVEE_CLIENT_ID")
    device_name = os.getenv("GOVEE_DEVICE_NAME")
    
    if not auth_token or not client_id or not device_name:
        raise HTTPException(status_code=500, detail="Missing required environment variables")
    
    temperature = await fetch_device_temperature(auth_token, client_id, device_name)
    
    if temperature is not None:
        return {"temperature": temperature}
    else:
        raise HTTPException(status_code=404, detail="Device not found or failed to fetch temperature")


def main():
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
