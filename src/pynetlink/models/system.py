"""System data models."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass
class DeviceInfo(DataClassDictMixin):
    """Device information from WebSocket `device.info` event or REST API.

    Attributes
    ----------
        device_id: Unique device identifier (BALENA_DEVICE_UUID or MAC address)
        device_name: Device name from Balena
        version: Netlink software version
        api_version: API version
        model: Device model (e.g., "NetOS Desk")
        mac_address: Device MAC address

    """

    device_id: str
    device_name: str
    version: str
    api_version: str
    model: str
    mac_address: str | None = None


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
