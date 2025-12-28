"""Asynchronous Python client for Netlink."""

from .const import (
    EVENT_BROWSER_STATE,
    EVENT_DESK_STATE,
    EVENT_DEVICE_INFO,
    EVENT_DISPLAY_STATE,
    EVENT_DISPLAYS_LIST,
    EVENT_SYSTEM_MQTT,
)
from .exceptions import (
    NetlinkAuthenticationError,
    NetlinkCommandError,
    NetlinkConnectionError,
    NetlinkDataError,
    NetlinkError,
    NetlinkTimeoutError,
)
from .models import (
    BrowserState,
    Desk,
    DeskState,
    DeviceInfo,
    Display,
    DisplayState,
    DisplaySummary,
    MQTTStatus,
    NetlinkDevice,
)
from .netlink import NetlinkClient

# Convenience aliases for discovery
discover_devices = NetlinkClient.discover_devices

__all__ = [
    "EVENT_BROWSER_STATE",
    "EVENT_DESK_STATE",
    "EVENT_DEVICE_INFO",
    "EVENT_DISPLAYS_LIST",
    "EVENT_DISPLAY_STATE",
    "EVENT_SYSTEM_MQTT",
    "BrowserState",
    "Desk",
    "DeskState",
    "DeviceInfo",
    "Display",
    "DisplayState",
    "DisplaySummary",
    "MQTTStatus",
    "NetlinkAuthenticationError",
    "NetlinkClient",
    "NetlinkCommandError",
    "NetlinkConnectionError",
    "NetlinkDataError",
    "NetlinkDevice",
    "NetlinkError",
    "NetlinkTimeoutError",
    "discover_devices",
]
