"""Data models for NetLink API."""

from __future__ import annotations

from .access_codes import AccessCode, AccessCodes, AuthMethod, AuthMethods
from .browser import BrowserState
from .desk import Desk, DeskState
from .discovery import NetlinkDevice
from .display import Display, DisplayState, DisplaySummary
from .system import DeviceInfo, MQTTStatus

__all__ = [
    "AccessCode",
    "AccessCodes",
    "AuthMethod",
    "AuthMethods",
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
