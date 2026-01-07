# Netlink API Reference

Based on: `blocks/netlink-webserver` implementation

> **Note**: This reference documents the current v1 API payloads used by pynetlink.

## WebSocket Events

### `device.info`
Sent via WebSocket with basic device information.

**Structure**:
```python
{
    "device_id": "abc123def456",        # str - unique device identifier
    "device_name": "Office Desk 1",     # str - device name
    "version": "develop",              # str - software version
    "api_version": "v1",               # str - API version
    "model": "NetOS Desk",             # str - device model
    "mac_address": "00:11:22:33:44:55" # str | None - MAC address (if provided)
}
```

### `desk.state`
Sent via WebSocket when desk state changes.

**Structure**:
```python
{
    "capabilities": {...},
    "inventory": {...},
    "state": {
        "height": 75.0,           # float - current height in cm
        "mode": "idle",           # str - operation mode (e.g., "idle", "moving", "stopped")
        "moving": False,          # bool - whether desk is moving
        "beep": "on",             # str | None - beep setting (may be present)
        "error": None,            # str | None - error message if any
        "target": 120.0,          # float | None - target height when moving
    }
}
```

**Notes**:
- NO `timestamp` field! This is added by WebServer's envelope, not in the data itself.
- `beep` field may be present in some events but is not in the TypedDict
- `error` is optional and may be `None`

### `display.state`
Sent via WebSocket when display state changes (individual display).

**Structure**:
```python
{
    "bus": 20,                  # int (or str) - I2C bus ID
    "model": "Dell U2723QE",    # str - display model
    "type": "monitor",          # str - device type
    "serial_number": "ABC123",  # str | None - serial number
    "supports": {...},           # dict - capabilities
    "source_options": [...],     # list[str] | None - available sources
    "state": {
        "power": "on",           # str | None - "on", "off", "standby"
        "source": "HDMI1",       # str | None - current input source
        "brightness": 72,         # int | None - brightness level (0-100)
        "volume": 50,             # int | None - volume level (0-100)
        "error": None,            # str | None - error message if any
    }
}
```

**Note**: NO separate timestamp field in data payload.

### `displays.list`
Sent via WebSocket with display summaries.

**Structure** (list of `DisplaySnapshot.to_summary()`):
```python
[
    {
        "id": 0,               # int - index in list
        "bus": 20,             # int - I2C bus ID
        "model": "Dell",       # str - display model
        "type": "monitor"      # str - device type
    }
]
```

### `browser.state`
Sent via WebSocket with browser state.

**Structure**:
```python
{
    "url": "https://example.com"  # str - current URL
}
```

### `system.mqtt`
Sent via WebSocket with MQTT connection status.

**Structure**:
```python
{
    "connected": True,            # bool
    "broker": "mqtt://..."        # str | None
}
```

---

## REST API Endpoints

### GET `/api/v1/device/info`
Returns basic device information.

**Response**:
```python
{
    "device_id": "abc123def456",        # str - unique device identifier
    "device_name": "Office Desk 1",     # str - device name
    "version": "develop",              # str - software version
    "api_version": "v1",               # str - API version
    "model": "NetOS Desk",             # str - device model
    "mac_address": "00:11:22:33:44:55" # str | None - MAC address (if provided)
}
```

### GET `/api/v1/desk/status`
Returns full desk status.

**Response**:
```python
{
    "capabilities": {...},
    "inventory": {...},
    "state": {
        "height": 95.0,
        "mode": "stopped",
        "moving": False,
        "error": None,
        "target": 110.0,
        "beep": "on",
    }
}
```

### POST `/api/v1/desk/height`
Set target desk height.

**Request**:
```python
{
    "height": 110.0    # float - target height (62-127 cm)
}
```

**Response**:
```python
{
    "height": 110.0,   # float - confirmed target
    "status": "ok"     # str - status
}
```

### POST `/api/v1/desk/beep`
Enable or disable the desk beep.

**Request**:
```python
{
    "state": "on"    # str - "on" or "off"
}
```

**Response**:
```python
{
    "status": "ok"   # str - status
}
```

### POST `/api/v1/desk/stop`
Stop desk movement.

**Response**:
```python
{
    "status": "ok"
}
```

### POST `/api/v1/desk/reset`
Reset desk to factory defaults.

**Response**:
```python
{
    "status": "ok"
}
```

### POST `/api/v1/desk/calibrate`
Start desk calibration.

**Response**:
```python
{
    "status": "ok"
}
```

### GET `/api/v1/displays`
List all connected displays.

**Response**:
```python
[
    {
        "id": 0,
        "bus": 20,
        "model": "Dell",
        "type": "display"
    }
]
```

### GET `/api/v1/display/{bus_id}/status`
Get detailed display status.

**Response**:
```python
{
    "bus": 20,
    "model": "Dell U2723QE",
    "type": "monitor",
    "serial_number": "ABC123XYZ",
    "supports": {"power": True, "brightness": True, ...},
    "source_options": ["HDMI1", "USBC"],
    "state": {
        "power": "on",
        "source": "HDMI1",
        "brightness": 72,
        "volume": 50,
        "error": None,
    }
}
```

### GET `/api/v1/display/{bus_id}/power`
Get display power state.

**Response**:
```python
{"state": "on"}
```

### PUT `/api/v1/display/{bus_id}/power`
Set display power state.

**Request**:
```python
{"state": "on"}
```

### GET `/api/v1/display/{bus_id}/source`
Get display input source.

**Response**:
```python
{"source": "HDMI1"}
```

### PUT `/api/v1/display/{bus_id}/source`
Set display input source.

**Request**:
```python
{"source": "HDMI1"}
```

### GET `/api/v1/display/{bus_id}/brightness`
Get display brightness.

**Response**:
```python
{"brightness": 72}
```

### PUT `/api/v1/display/{bus_id}/brightness`
Set display brightness.

**Request**:
```python
{"brightness": 72}
```

### GET `/api/v1/display/{bus_id}/volume`
Get display volume.

**Response**:
```python
{"volume": 50}
```

### PUT `/api/v1/display/{bus_id}/volume`
Set display volume.

**Request**:
```python
{"volume": 50}
```

### PATCH `/api/v1/display/{bus_id}`
Update multiple display properties at once.

**Request**:
```python
{
    "power": "on",
    "brightness": 72,
    "volume": 50,
    "source": "HDMI1",
}
```

### GET `/api/v1/browser/url`
Get current browser URL.

**Response**:
```python
{"url": "https://example.com"}
```

### POST `/api/v1/browser/url`
Set browser URL.

**Request**:
```python
{"url": "https://example.com"}
```

### GET `/api/v1/browser/status`
Get browser status.

**Response**:
```python
{"url": "https://example.com"}
```

### POST `/api/v1/browser/refresh`
Refresh browser.

**Response**:
```python
{"status": "ok"}
```

---

## Key Differences from Documentation

1. **NO `timestamp` in data payloads** - timestamps are in WebSocket envelope, not data
2. **WebSocket payload often wrapped in `data`** - pynetlink unwraps and passes the inner payload
3. **Desk and display state are nested under `state`** - not flattened
4. **Display `bus` can be int or str** - needs flexible handling
5. **Display serial key is `serial_number`** - not `sn`

---

## WebSocket Envelope Format

According to Phase 1 documentation, WebSocket events have envelope:

```python
{
    "type": "desk.state",      # str - event name
    "data": {...},             # dict - actual payload (DeskSnapshot or DisplaySnapshot)
    "ts": "2025-12-10T12:00:00Z"  # str - ISO8601 timestamp
}
```

**Important Notes**:
- The `timestamp` is in the envelope `ts` field, NOT in the data dict!
- The `pynetlink` library automatically extracts the `data` field before passing it to your callbacks
- You receive the unwrapped payload directly, not the full envelope
- If you need the timestamp, you can access it via the raw Socket.IO event (advanced usage)

---

## WebSocket Commands

> **Status**: ✅ Implemented in pynetlink
> **Current**: REST is available as fallback (see above)

The netlink-webserver supports a modern WebSocket command system with acknowledgements.

### Command Format

**Client sends**:
```python
{
  "type": "command.desk.height",     # Command type
  "id": "550e8400-e29b-41d4-a716-446655440000",  # Unique request ID (UUID)
  "data": {                          # Command-specific data
    "height": 120.0
  }
}
```

**Server responds with acknowledgement**:
```python
{
  "type": "command_ack",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",  # Same ID as request
    "status": "ok",                  # "ok" or "error"
    "error": null                    # Error message if status is "error"
  },
  "ts": "2025-12-10T12:00:00Z"
}
```

### Supported Commands

| Command Type | Data Fields | Description |
|-------------|-------------|-------------|
| `command.desk.height` | `{"height": float}` | Set desk height (62-127 cm) |
| `command.desk.stop` | `{}` | Stop desk movement |
| `command.desk.reset` | `{}` | Reset desk to factory defaults |
| `command.desk.calibrate` | `{}` | Start desk calibration |
| `command.desk.beep` | `{"state": "on"\|"off"}` | Set desk beep |
| `command.display.power` | `{"bus": "20", "attr": "power", "value": "on"}` | Set display power |
| `command.display.source` | `{"bus": "20", "attr": "source", "value": "HDMI1"}` | Set display input source |
| `command.display.brightness` | `{"bus": "20", "attr": "brightness", "value": 72}` | Set display brightness (0-100) |
| `command.display.volume` | `{"bus": "20", "attr": "volume", "value": 50}` | Set display volume (0-100) |
| `command.browser.url` | `{"url": "https://example.com"}` | Set browser URL |
| `command.browser.refresh` | `{}` | Refresh browser page |

### Error Codes

The `command_ack` may include these error statuses:

| Status | Description |
|--------|-------------|
| `ok` | Command executed successfully |
| `error` | Command failed (see `error` field for details) |

Common error messages:
- `"Invalid height range"` - Height out of 62-127 cm range
- `"Desk not connected"` - Desk controller not available
- `"Display not found"` - Invalid display bus ID
- `"Command timeout"` - Command execution timeout (5s)

### Transport Selection (pynetlink)

```python
from pynetlink import NetlinkClient

async with NetlinkClient(host, token) as client:
    await client.connect()

    # Uses WebSocket when connected; falls back to REST when not connected
    await client.set_desk_height(120.0, transport="auto")

    # Force specific transport
    await client.set_desk_height(120.0, transport="websocket")
    await client.set_desk_height(120.0, transport="rest")
```
