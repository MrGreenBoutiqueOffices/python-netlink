"""System data models."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass
class SystemInfo(DataClassDictMixin):
    """System information from WebSocket `system.info` event.

    Attributes
    ----------
        version: Netlink software version
        api_version: API version
        device_id: Unique device identifier
        device_name: Device name
        uptime: System uptime in seconds

    """

    version: str
    api_version: str
    device_id: str
    device_name: str
    uptime: int


@dataclass
class MQTTStatus(DataClassDictMixin):
    """MQTT connection status from WebSocket `system.mqtt` event.

    Attributes
    ----------
        connected: Whether MQTT is connected
        broker: MQTT broker address

    """

    connected: bool
    broker: str | None = None
