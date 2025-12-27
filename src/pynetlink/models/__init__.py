"""Data models for Netlink API."""

from __future__ import annotations

from .browser import BrowserState
from .desk import Desk, DeskState
from .discovery import NetlinkDevice
from .display import Display, DisplayState, DisplaySummary
from .system import DeviceInfo, MQTTStatus

__all__ = [
    "BrowserState",
    "Desk",
    "DeskState",
    "DeviceInfo",
    "Display",
    "DisplayState",
    "DisplaySummary",
    "MQTTStatus",
    "NetlinkDevice",
]
