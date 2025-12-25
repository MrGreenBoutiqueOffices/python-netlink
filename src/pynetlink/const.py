"""Constants for pynetlink."""

from __future__ import annotations

# Default timeouts
DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_REQUEST_TIMEOUT = 5.0
DEFAULT_COMMAND_TIMEOUT = 5.0
DEFAULT_RECONNECT_DELAY = 1.0
MAX_RECONNECT_DELAY = 60.0

# WebSocket events
EVENT_DESK_STATE = "desk.state"
EVENT_DISPLAY_STATE = "display.state"
EVENT_DISPLAYS_LIST = "displays.list"
EVENT_BROWSER_STATE = "browser.state"
EVENT_DEVICE_INFO = "device.info"
EVENT_SYSTEM_MQTT = "system.mqtt"

# API endpoints
API_VERSION = "v1"

# Discovery
MDNS_SERVICE_TYPE = "_netlink._tcp.local."
