"""Data models for Netlink API."""

from __future__ import annotations

from .browser import BrowserState
from .desk import DeskState, DeskStatus
from .discovery import NetlinkDevice
from .monitor import MonitorState, MonitorSummary
from .system import DeviceInfo, MQTTStatus

__all__ = [
    "BrowserState",
    "DeskState",
    "DeskStatus",
    "DeviceInfo",
    "MQTTStatus",
    "MonitorState",
    "MonitorSummary",
    "NetlinkDevice",
]
