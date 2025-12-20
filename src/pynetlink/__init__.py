"""Asynchronous Python client for Netlink."""

from .const import (
    EVENT_BROWSER_STATE,
    EVENT_DESK_STATE,
    EVENT_DEVICE_INFO,
    EVENT_MONITOR_STATE,
    EVENT_MONITORS_LIST,
    EVENT_SYSTEM_MQTT,
)
from .exceptions import (
    NetlinkAuthenticationError,
    NetlinkCommandError,
    NetlinkConnectionError,
    NetlinkError,
    NetlinkTimeoutError,
)
from .models import (
    BrowserState,
    DeskState,
    DeskStatus,
    DeviceInfo,
    MonitorState,
    MonitorSummary,
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
    "EVENT_MONITORS_LIST",
    "EVENT_MONITOR_STATE",
    "EVENT_SYSTEM_MQTT",
    "BrowserState",
    "DeskState",
    "DeskStatus",
    "DeviceInfo",
    "MQTTStatus",
    "MonitorState",
    "MonitorSummary",
    "NetlinkAuthenticationError",
    "NetlinkClient",
    "NetlinkCommandError",
    "NetlinkConnectionError",
    "NetlinkDevice",
    "NetlinkError",
    "NetlinkTimeoutError",
    "discover_devices",
]
