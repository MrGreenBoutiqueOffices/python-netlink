"""Data models for Netlink API."""

from __future__ import annotations

from .browser import BrowserState
from .desk import DeskState, DeskStatus
from .discovery import NetlinkDevice
from .monitor import MonitorState, MonitorSummary
from .system import MQTTStatus, SystemInfo

__all__ = [
    "BrowserState",
    "DeskState",
    "DeskStatus",
    "MQTTStatus",
    "MonitorState",
    "MonitorSummary",
    "NetlinkDevice",
    "SystemInfo",
]
