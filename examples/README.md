# Pynetlink Examples

Complete usage examples for the `pynetlink` library.

## Table of Contents

- [Setup](#setup)
- [Quick Start](#quick-start)
- [Example Files](#example-files)
- [Device Discovery](#device-discovery)
- [Real-time Events](#real-time-events)
- [Desk Control](#desk-control)
- [Display Control](#display-control)
- [Browser Control](#browser-control)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)

---

## Setup

Before running the examples, configure your Netlink device credentials:

1. Copy the example environment file:
   ```bash
   cp examples/.env.example examples/.env
   ```

2. Edit `examples/.env` and add your device details:
   ```bash
   NETLINK_HOST=192.168.1.100
   NETLINK_TOKEN=your-actual-token-here
   ```

3. Install dependencies (if running examples locally):
   ```bash
   poetry install
   ```

All examples will automatically load credentials from the `.env` file.

---

## Example Files

This directory contains the following runnable examples:

### [`quickstart/basic_usage.py`](./quickstart/basic_usage.py)
Comprehensive quickstart demonstrating WebSocket + REST flow.

### [`discovery/discover_devices.py`](./discovery/discover_devices.py)
Device discovery example using mDNS/Zeroconf.

### [`realtime/desk_state_listener.py`](./realtime/desk_state_listener.py)
Focused real-time desk displaying example.

### [`realtime/display_state_listener.py`](./realtime/display_state_listener.py)
Real-time display state listener per bus.

### [`rest/rest_only.py`](./rest/rest_only.py)
REST-only desk and display control.

### [`rest/browser_control.py`](./rest/browser_control.py)
Browser control endpoints via REST.

## Quick Start

Basic example showing connection and desk control:

```python
import asyncio
from pynetlink import NetlinkClient

async def main() -> None:
    """Quick start example."""
    # Create client with device IP and bearer token
    async with NetlinkClient("192.0.2.10", "your-token") as client:
        # Connect WebSocket for real-time updates
        await client.connect()

        # Get current desk state from WebSocket
        if client.desk_state:
            print(f"Desk height: {client.desk_state.height}cm")
            print(f"Mode: {client.desk_state.mode}")

        # Set desk height
        await client.set_desk_height(120.0)
        print("Desk moving to 120cm...")

        # Control display
        displays = await client.get_displays()
        if displays:
            await client.set_display_brightness(displays[0].bus, 80)
            print("Display brightness set to 80%")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Device Discovery

Automatically find Netlink devices on your network using mDNS/Zeroconf:

### Basic Discovery

```python
from pynetlink import NetlinkClient

async def discover() -> None:
    """Discover all Netlink devices."""
    print("Discovering devices...")
    devices = await NetlinkClient.discover_devices(timeout=5.0)

    if not devices:
        print("No devices found!")
        return

    for device in devices:
        print(f"\nDevice: {device.name}")
        print(f"  Host: {device.host}:{device.port}")
        print(f"  Device ID: {device.device_id}")
        print(f"  Model: {device.model}")
        print(f"  Version: {device.version}")
        print(f"  Has desk: {device.has_desk}")
        print(f"  Displays: {', '.join(device.displays)}")
```

### Connect to First Discovered Device

```python
async def auto_connect() -> None:
    """Auto-connect to first discovered device."""
    devices = await NetlinkClient.discover_devices()

    if not devices:
        print("No devices found!")
        return

    device = devices[0]
    print(f"Connecting to {device.name} at {device.host}...")

    # Note: You still need the bearer token!
    async with NetlinkClient(device.host, "your-token") as client:
        await client.connect()
        print(f"Connected! Desk: {client.desk_state}")
```

**See**: [`discovery/discover_devices.py`](./discovery/discover_devices.py) for complete example.

---

## Real-time Events

Subscribe to WebSocket events for real-time state updates:

### Subscribe to All Events

```python
from pynetlink import (
    NetlinkClient,
    EVENT_DESK_STATE,
    EVENT_DEVICE_INFO,
    EVENT_MONITOR_STATE,
)

async def listen_all_events() -> None:
    """Listen to all WebSocket events."""
    async with NetlinkClient(host, token) as client:
        await client.connect()

        @client.on(EVENT_DESK_STATE)
        async def on_desk_state(data: dict) -> None:
            """Desk state changed."""
            state = data.get("state", data)
            print(f"📊 Desk: {state['height']}cm, {state['mode']}")
            if state.get('moving'):
                print(f"  → Target: {state.get('target')}cm")

        @client.on(EVENT_MONITOR_STATE)
        async def on_display_state(_raw_data: dict) -> None:
            """Display state changed - use client.displays for parsed data."""
            for bus_id, display in client.displays.items():
                print(f"🖥️  Display {bus_id} ({display.model}):")
                print(f"  Power: {display.state.power}")
                print(f"  Brightness: {display.state.brightness}%")
                print(f"  Volume: {display.state.volume}%")
                print(f"  Source: {display.state.source}")

        @client.on("displays.list")
        async def on_displays_list(data: list) -> None:
            """Display list updated."""
            print(f"📋 Displays: {len(data)} connected")

        @client.on(EVENT_DEVICE_INFO)
        async def on_device_info(data: dict) -> None:
            """Device info received."""
            print(f"ℹ️  Device: {data['device_name']} ({data['model']})")

        # Keep connection alive to receive events
        print("Listening for events... (press Ctrl+C to stop)")
        await asyncio.sleep(3600)  # 1 hour
```

### Using Cached State

Access the latest state without callbacks:

```python
async def use_cached_state() -> None:
    """Use cached WebSocket state."""
    async with NetlinkClient(host, token) as client:
        await client.connect()

        # Wait for initial events
        await asyncio.sleep(1)

        # Access cached desk state
        if client.desk_state:
            print(f"Height: {client.desk_state.height}cm")
            print(f"Mode: {client.desk_state.mode}")
            print(f"Moving: {client.desk_state.moving}")
            print(f"Error: {client.desk_state.error or 'None'}")

        # Access cached device info
        if client.device_info:
            print(f"\nDevice: {client.device_info.device_name}")
            print(f"  Model: {client.device_info.model}")
            print(f"  Version: {client.device_info.version}")

        # Access cached display states
        for bus_id, display in client.displays.items():
            print(f"\nDisplay {bus_id}:")
            print(f"  Model: {display.model}")
            print(f"  Serial: {display.serial_number}")
            print(f"  Power: {display.state.power}")
            print(f"  Source: {display.state.source}")
            print(f"  Brightness: {display.state.brightness}%")
            print(f"  Volume: {display.state.volume}%")
```

**See**: [`quickstart/basic_usage.py`](./quickstart/basic_usage.py) for event handling example.

---

## Desk Control

Control your standing desk via REST API:

### Get Desk Status

```python
async def get_desk_info() -> None:
    """Get full desk status."""
    async with NetlinkClient(host, token) as client:
        # Get status via REST API
        desk = await client.get_desk_status()

        print(f"Desk Status:")
        print(f"  Height: {desk.state.height}cm")
        print(f"  Mode: {desk.state.mode}")
        print(f"  Moving: {desk.state.moving}")
        print(f"  Error: {desk.state.error or 'None'}")
```

### Set Desk Height

```python
async def move_desk() -> None:
    """Move desk to specific height."""
    async with NetlinkClient(host, token) as client:
        await client.connect()

        # Subscribe to track movement
        @client.on("desk.state")
        async def on_desk_state(data: dict) -> None:
            state = data.get("state", data)
            if state['moving']:
                print(f"Moving... {state['height']}cm → {state['target']}cm")
            else:
                print(f"Stopped at {state['height']}cm")

        # Set target height (62-127 cm)
        print("Setting height to 120cm...")
        await client.set_desk_height(120.0)

        # Wait for movement to complete
        await asyncio.sleep(10)
```

### Stop Desk Movement

```python
async def emergency_stop() -> None:
    """Stop desk immediately."""
    async with NetlinkClient(host, token) as client:
        print("Stopping desk...")
        await client.stop_desk()
        print("Stopped!")
```

### Calibrate Desk

```python
async def calibrate() -> None:
    """Calibrate desk (reset min/max heights)."""
    async with NetlinkClient(host, token) as client:
        print("Starting calibration...")
        print("Follow desk controller instructions")
        await client.calibrate_desk()
```

### Desk Presets

```python
async def desk_presets() -> None:
    """Move to preset heights."""
    SITTING = 75.0   # cm
    STANDING = 120.0  # cm

    async with NetlinkClient(host, token) as client:
        # Move to sitting position
        print("Moving to sitting position...")
        await client.set_desk_height(SITTING)
        await asyncio.sleep(5)

        # Move to standing position
        print("Moving to standing position...")
        await client.set_desk_height(STANDING)
        await asyncio.sleep(5)
```

---

## Display Control

Control DDC/CI compatible displays:

### List Displays

```python
async def list_displays() -> None:
    """Get list of all connected displays."""
    async with NetlinkClient(host, token) as client:
        displays = await client.get_displays()

        print(f"Found {len(displays)} display(s):\n")
        for display in displays:
            print(f"Display {display.id}:")
            print(f"  Bus ID: {display.bus}")
            print(f"  Model: {display.model}")
            print(f"  Type: {display.type}")
```

### Get Display Status

```python
async def display_status() -> None:
    """Get detailed display status."""
    async with NetlinkClient(host, token) as client:
        status = await client.get_display_status(bus_id=0)

        print(f"Display Status:")
        print(f"  Bus: {status.bus}")
        print(f"  Model: {status.model}")
        print(f"  Type: {status.type}")
        print(f"  Serial: {status.serial_number}")
        print(f"  Power: {status.state.power}")
        print(f"  Source: {status.state.source}")
        print(f"  Brightness: {status.state.brightness}%")
        print(f"  Volume: {status.state.volume}%")
        print(f"  Capabilities: {status.supports}")
        print(f"  Available sources: {status.source_options}")
```

### Control Display Power

```python
async def control_power() -> None:
    """Turn display on/off."""
    async with NetlinkClient(host, token) as client:
        # Turn on
        await client.set_display_power(bus_id=0, state="on")
        print("Display powered ON")

        await asyncio.sleep(5)

        # Turn off
        await client.set_display_power(bus_id=0, state="off")
        print("Display powered OFF")
```

### Adjust Brightness

```python
async def adjust_brightness() -> None:
    """Adjust display brightness."""
    async with NetlinkClient(host, token) as client:
        # Set to 100% (max)
        await client.set_display_brightness(bus_id=0, brightness=100)
        print("Brightness: 100%")

        await asyncio.sleep(2)

        # Gradually dim to 20%
        for level in range(100, 19, -10):
            await client.set_display_brightness(bus_id=0, brightness=level)
            print(f"Brightness: {level}%")
            await asyncio.sleep(0.5)
```

### Change Input Source

```python
async def switch_source() -> None:
    """Switch display input source."""
    async with NetlinkClient(host, token) as client:
        # Get available sources
        status = await client.get_display_status(bus_id=0)
        print(f"Available sources: {status.source_options}")

        # Switch to HDMI1
        await client.set_display_source(bus_id=0, source="HDMI1")
        print("Switched to HDMI1")

        await asyncio.sleep(2)

        # Switch to USB-C
        await client.set_display_source(bus_id=0, source="USBC")
        print("Switched to USB-C")
```

### Control Multiple Properties

```python
async def batch_update() -> None:
    """Update multiple display properties at once."""
    async with NetlinkClient(host, token) as client:
        # Using individual methods
        await client.set_display_power(0, "on")
        await client.set_display_brightness(0, 80)
        await client.set_display_volume(0, 50)

        print("Display configured!")
```

---

## Browser Control

Control the browser container (if available on your Netlink device):

### Get Current URL

```python
async def get_url() -> None:
    """Get current browser URL."""
    async with NetlinkClient(host, token) as client:
        url = await client.get_browser_url()
        print(f"Current URL: {url}")
```

### Navigate to URL

```python
async def navigate() -> None:
    """Navigate browser to specific URL."""
    async with NetlinkClient(host, token) as client:
        await client.set_browser_url("https://example.com")
        print("Browser navigated to example.com")
```

### Refresh Page

```python
async def refresh() -> None:
    """Refresh browser page."""
    async with NetlinkClient(host, token) as client:
        await client.refresh_browser()
        print("Page refreshed!")
```

### Get Browser Status

```python
async def browser_status() -> None:
    """Get full browser status."""
    async with NetlinkClient(host, token) as client:
        status = await client.get_browser_status()
        print(f"URL: {status.url}")
        print(f"Status: {status.status}")  # loading, ready, error
```

---

## Error Handling

Handle different error scenarios:

### Authentication Errors

```python
from pynetlink import NetlinkClient, NetlinkAuthenticationError

async def handle_auth_error() -> None:
    """Handle invalid token."""
    try:
        async with NetlinkClient(host, "invalid-token") as client:
            await client.connect()
    except NetlinkAuthenticationError:
        print("❌ Invalid bearer token!")
        print("Get token from Balena dashboard or device config")
```

### Connection Errors

```python
from pynetlink import NetlinkConnectionError, NetlinkTimeoutError

async def handle_connection_errors() -> None:
    """Handle connection issues."""
    try:
        async with NetlinkClient("192.168.1.999", token) as client:
            await client.connect()
    except NetlinkTimeoutError:
        print("⏱️  Connection timed out")
    except NetlinkConnectionError as e:
        print(f"🔌 Connection failed: {e}")
```

### Command Errors

```python
from pynetlink import NetlinkCommandError

async def handle_command_errors() -> None:
    """Handle command execution errors."""
    async with NetlinkClient(host, token) as client:
        try:
            # Try invalid height
            await client.set_desk_height(200.0)
        except ValueError as e:
            print(f"❌ Invalid value: {e}")

        try:
            # Try invalid brightness
            await client.set_display_brightness(0, 150)
        except ValueError as e:
            print(f"❌ Invalid value: {e}")
```

### Comprehensive Error Handling

```python
from pynetlink import (
    NetlinkError,
    NetlinkAuthenticationError,
    NetlinkConnectionError,
    NetlinkTimeoutError,
)

async def comprehensive_error_handling() -> None:
    """Handle all error types."""
    try:
        async with NetlinkClient(host, token) as client:
            await client.connect()
            await client.set_desk_height(120.0)

    except NetlinkAuthenticationError:
        print("❌ Authentication failed - check token")
    except NetlinkTimeoutError:
        print("⏱️  Request timed out - check network")
    except NetlinkConnectionError as e:
        print(f"🔌 Connection error: {e}")
    except NetlinkError as e:
        print(f"⚠️  Netlink error: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
```

---

## Advanced Usage

### Custom Timeout

```python
async def custom_timeout() -> None:
    """Use custom request timeout."""
    # Default is 5 seconds
    async with NetlinkClient(host, token, request_timeout=10.0) as client:
        await client.connect()
        # Slower operations now have 10 second timeout
```

### Shared aiohttp Session

```python
import aiohttp

async def shared_session() -> None:
    """Use shared aiohttp session."""
    async with aiohttp.ClientSession() as session:
        client = NetlinkClient(host, token, session=session)

        await client.connect()
        # Client uses provided session
        await client.disconnect()
        # Session remains open for other uses
```

### Multiple Devices

```python
async def control_multiple_devices() -> None:
    """Control multiple Netlink devices."""
    devices = [
        ("192.0.2.10", "token1"),
        ("192.0.2.11", "token2"),
    ]

    clients = []
    for host, token in devices:
        client = NetlinkClient(host, token)
        await client.connect()
        clients.append(client)

    # Control all desks simultaneously
    await asyncio.gather(*[
        client.set_desk_height(120.0)
        for client in clients
    ])

    # Cleanup
    await asyncio.gather(*[
        client.disconnect()
        for client in clients
    ])
```

### Context-Free Usage

```python
async def without_context_manager() -> None:
    """Use client without context manager."""
    client = NetlinkClient(host, token)

    try:
        await client.connect()
        await client.set_desk_height(110.0)
    finally:
        # Always cleanup!
        await client.disconnect()
```

---

## Data Models

All responses use type-safe dataclasses with [mashumaro](https://github.com/Fatal1ty/mashumaro):

### DeskState (WebSocket)

```python
@dataclass
class DeskState:
    height: float              # Current height in cm
    mode: str                  # "idle", "moving_up", "moving_down", etc.
    moving: bool               # Is desk currently moving
    error: str                 # Error message if any
    target: float | None       # Target height when moving
    capabilities: dict | None  # Desk capabilities
    inventory: dict | None     # Desk inventory info
```

### Display (WebSocket)

```python
@dataclass
class DisplayState:
    """Current state values (nested in Display)."""
    power: str | None               # "on", "off"
    source: str | None              # "HDMI1", "USBC", etc.
    brightness: int | None          # 0-100
    volume: int | None              # 0-100
    error: str | None               # Error message if any

@dataclass
class Display:
    """Full display information with capabilities and state."""
    bus: int | str                   # I2C bus ID
    model: str                       # Display model
    type: str                        # "display", "tablet"
    supports: dict[str, Any]         # Capabilities (e.g., {"power": True, "brightness": True})
    state: DisplayState              # Nested current state values
    serial_number: str | None        # Serial number
    source_options: list[str] | None # Available input sources
```

**Breaking Change (v0.2.0)**: Display now has a nested structure:
- Capabilities are at the top level (`model`, `type`, `supports`, `serial_number`)
- Runtime values are nested under `state` (`.state.power`, `.state.brightness`, etc.)
- `sn` renamed to `serial_number`
- `supports.source` is now a boolean (was list of sources, now in `source_options`)

### NetlinkDevice (Discovery)

```python
@dataclass
class NetlinkDevice:
    name: str            # Device name
    host: str            # IP address
    port: int            # Port (usually 80)
    device_id: str       # Unique ID
    model: str           # Device model
    version: str         # Software version
    api_version: str     # API version
    has_desk: bool       # Has desk control
    displays: list[str]  # Display bus IDs
    ws_path: str         # WebSocket path
```

---

## Authentication

### Getting Your Bearer Token

The bearer token is required for all API calls. You can find it in:

1. **Balena Dashboard**:
   - Go to your device
   - Navigate to "Device Variables"
   - Look for `REST_BEARER_TOKEN`

2. **Device SSH**:
   ```bash
   balena ssh <uuid>
   balena envs | grep REST_BEARER_TOKEN
   ```

3. **Future Options** (planned):
   - QR code scanning
   - Time-limited pairing mode (like Philips Hue)

### Security Note

⚠️ **Keep your token secret!** Don't commit it to version control or share it publicly.

Store it in environment variables:

```python
import os
from pynetlink import NetlinkClient

TOKEN = os.getenv("NETLINK_TOKEN")
client = NetlinkClient("192.0.2.10", TOKEN)
```

---

## Future: WebSocket Commands (v0.2.0)

> **Current**: All commands use REST API
> **Future**: Commands will use WebSocket with acknowledgements

The netlink-webserver already supports WebSocket commands. In v0.2.0, the library will use WebSocket as the primary transport for all commands, with REST as fallback.

**Benefits**:
- ⚡ Faster response (no HTTP roundtrip)
- 🔄 Real-time acknowledgements
- 📡 Single persistent connection for everything

See [`ROADMAP.md`](../ROADMAP.md) for details and timeline.

---

## Contributing

Have a useful example? Submit a PR! We especially welcome examples for:

- Integration with automation systems
- Scheduled desk/display control
- Health monitoring and alerts
- Multi-device coordination
- WebSocket command implementation (v0.2.0)

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for guidelines.
