# Govee Temperature Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![HACS][hacsbadge]][hacs]

A robust Home Assistant custom integration that provides temperature, humidity, and battery monitoring for Govee devices through the official mobile app API.

## ✨ Features

- **🔍 Automatic Device Discovery**: Automatically finds and configures all Govee temperature/humidity sensors
- **📊 Multi-Sensor Support**: Temperature, humidity, and battery level monitoring
- **🎯 Entity Categories**: Battery sensors properly categorized as diagnostic entities
- **🔧 Easy Configuration**: User-friendly setup through Home Assistant's config flow UI
- **📱 Real Device Info**: Shows actual device models and hardware versions
- **🔄 Reliable Updates**: Configurable polling with built-in error handling and authentication recovery
- **🏠 HACS Compatible**: Easy installation and updates through HACS

## 📋 Requirements

- Home Assistant 2024.1.0 or newer
- iOS device with Govee Home app
- Proxyman or similar HTTPS proxy tool for credential extraction

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Navigate to **Integrations**
3. Click the **⋮** menu and select **Custom repositories**
4. Add repository: `https://github.com/DouweM/govee-temperature`
5. Category: **Integration**
6. Click **Add** → Find **Govee Temperature** → **Install**
7. Restart Home Assistant

### Option 2: Manual Installation

1. Download the `custom_components/govee_temperature/` folder
2. Copy to your HA `custom_components/` directory
3. Restart Home Assistant

## 🔑 Getting Govee Credentials

### Using Proxyman (iOS)

1. **Install Proxyman**: Download [Proxyman](https://proxyman.io/ios) on your iOS device
2. **Configure SSL Proxying**: 
   - Open Proxyman → **More** → **SSL Proxying List**
   - Add `app2.govee.com` to the list
3. **Install Certificates**: Follow Proxyman's instructions to install the profile and certificate
4. **Capture Traffic**: 
   - Enable Proxyman VPN
   - Open Govee Home app
   - Navigate to any temperature sensor
5. **Extract Credentials**:
   - In Proxyman, find the request to `https://app2.govee.com/bff-app/v1/device/list`
   - Copy the `Authorization` header value (starts with "Bearer ")
   - Copy the `clientId` header value

### Alternative Methods

- **Android**: Use HTTP Toolkit, Charles Proxy, or similar tools
- **Network Level**: Configure a proxy on your router (advanced)

## ⚙️ Configuration

1. **Add Integration**:
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for "Govee Temperature"

2. **Enter Credentials**:
   - **Authorization Bearer Token**: The full Bearer token from the Authorization header
   - **Client ID**: The clientId header value
   - **Update Interval**: How often to fetch data (60-3600 seconds, default: 300)

3. **Complete Setup**: The integration will validate credentials and discover all available devices

## 📊 Entities Created

For each discovered Govee device, the integration creates:

| Entity | Description | Device Class | Category |
|--------|-------------|--------------|----------|
| `sensor.<device_name>_temperature` | Temperature in °C | Temperature | Primary |
| `sensor.<device_name>_humidity` | Humidity percentage | Humidity | Primary |
| `sensor.<device_name>_battery` | Battery level percentage | Battery | Diagnostic |

## 🏷️ Supported Device Models

The integration automatically detects and properly identifies these Govee models:

- **H5051**: WiFi Thermo-Hygrometer
- **H5074**: Bluetooth Thermo-Hygrometer
- **H5075**: Bluetooth Thermo-Hygrometer
- **H5101**: WiFi Thermo-Hygrometer
- **H5102**: WiFi Thermo-Hygrometer
- **H5179**: WiFi Thermo-Hygrometer

*Unknown models will be detected as generic sensors with proper functionality.*

## 🔧 Advanced Configuration

### Update Intervals

- **Minimum**: 60 seconds (to respect API rate limits)
- **Default**: 300 seconds (5 minutes)
- **Recommended**: 300-600 seconds for optimal balance of freshness and API usage

### Authentication Recovery

The integration automatically handles:
- Expired tokens (triggers re-authentication prompt)
- Network connectivity issues (automatic retry)
- Temporary API outages (graceful degradation)

## 🐛 Troubleshooting

### Common Issues

**"Cannot Connect" Error**:
- Verify your Bearer token is complete and starts with "Bearer "
- Ensure your Client ID is correct
- Check that your Govee app is working normally

**"No Devices Found"**:
- Make sure you have temperature sensors in your Govee account
- Verify the sensors are online in the Govee app
- Try refreshing the device list in the Govee app

**Authentication Failures**:
- Tokens may expire - re-extract credentials using Proxyman
- Ensure you're using the latest credentials from a fresh app session

### Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.govee_temperature: debug
```

## 🔄 API Usage

- **Endpoint**: `https://app2.govee.com/bff-app/v1/device/list`
- **Rate Limiting**: Respects API limits with minimum 60-second intervals
- **Data Usage**: Minimal - only fetches device list and current readings

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the linting and formatting tools:
   ```bash
   # Install dev dependencies
   uv sync --extra dev
   
   # Format code
   uv run ruff format .
   
   # Check and fix linting issues
   uv run ruff check . --fix
   
   # Run type checking
   uv run pyright
   ```
5. Add tests if applicable
6. Submit a pull request

### Development Tools

This project uses:
- **[Ruff](https://docs.astral.sh/ruff/)**: Fast Python linter and formatter
- **[Pyright](https://github.com/microsoft/pyright)**: Static type checker
- **[uv](https://github.com/astral-sh/uv)**: Fast Python package manager

### Code Quality Standards

- **Line Length**: 100 characters
- **Type Hints**: Required for all public functions
- **Import Style**: Single-line imports, first-party packages listed
- **Exception Chaining**: Use `raise ... from err` for proper error context

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [govee_h5042_sensor](https://github.com/clong/govee_h5042_sensor)
- Built with Home Assistant's modern integration patterns
- Thanks to the Home Assistant community for excellent documentation
- **🤖 This integration was entirely generated by [Claude](https://claude.ai/code)** - AI-powered development from initial concept to production-ready Home Assistant integration

## 🌐 Web API Usage

The integration includes a standalone web API for non-Home Assistant usage.

### Starting the API Server

```bash
# Set environment variables
export GOVEE_AUTH_TOKEN="your_bearer_token"
export GOVEE_CLIENT_ID="your_client_id"
export GOVEE_DEVICE_NAME="your_device_name"  # Optional, for /temperature endpoint

# Install and run
uv sync
uv run govee-temperature
```

### API Endpoints

| Endpoint | Description | Response |
|----------|-------------|----------|
| `GET /temperature` | Get temperature from configured device | `{"temperature": 23.45}` |
| `GET /devices` | List all temperature/humidity devices | Array of device objects |
| `GET /device/{name}` | Get specific device by name | Device object with all sensor data |
| `GET /health` | Health check | `{"status": "healthy"}` |

### Python Library Usage

```python
from govee_temperature import GoveeClient

# Initialize client
client = GoveeClient(
    auth_token="your_bearer_token",
    client_id="your_client_id"
)

# Get all devices
devices = await client.get_devices()
for device in devices:
    print(f"{device.name}: {device.data.temperature}°C")

# Get specific device
device = await client.get_device_by_name("Living Room")
if device:
    print(f"Temperature: {device.data.temperature}°C")
    print(f"Humidity: {device.data.humidity}%")
    print(f"Battery: {device.data.battery}%")
```

## 🏗️ Architecture

This project provides two ways to access Govee temperature data:

1. **Home Assistant Integration** (`custom_components/govee_temperature/`)
   - Uses an embedded client for maximum compatibility
   - No external dependencies beyond Home Assistant requirements
   - Proper HA exception handling and configuration flow

2. **Standalone Web API** (`govee_temperature/`)
   - Uses the shared `govee_temperature` Python package
   - FastAPI-based REST endpoints
   - Can be used independently or alongside HA integration

## 📚 Related Projects

- **Python Client Library**: The `govee_temperature` package provides a reusable client for non-HA usage
- **Docker Support**: Pre-built images available at `ghcr.io/douwem/govee-temperature`

---

[releases-shield]: https://img.shields.io/github/release/DouweM/govee-temperature.svg?style=for-the-badge
[releases]: https://github.com/DouweM/govee-temperature/releases
[license-shield]: https://img.shields.io/github/license/DouweM/govee-temperature.svg?style=for-the-badge
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration