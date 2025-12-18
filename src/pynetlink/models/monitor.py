"""Monitor data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mashumaro import DataClassDictMixin


@dataclass
class MonitorState(DataClassDictMixin):
    """Real-time monitor state from WebSocket `monitor.state` event.

    Based on MonitorSnapshot.to_status() from netlink-webserver.

    Attributes
    ----------
        bus: Monitor I2C bus ID (can be int or str)
        power: Current power state ("on", "off", "standby")
        source: Current input source (e.g., "HDMI1", "USBC")
        brightness: Current brightness level (0-100)
        volume: Current volume level (0-100)
        model: Monitor model name
        type: Device type ("monitor", "tablet")
        sn: Serial number
        supports: Monitor capabilities dict
        source_options: List of available input sources

    """

    bus: int | str
    power: str | None = None
    source: str | None = None
    brightness: int | None = None
    volume: int | None = None
    model: str | None = None
    type: str | None = None
    sn: str | None = None
    supports: dict[str, Any] | None = None
    source_options: list[str] | None = None

    def __post_init__(self) -> None:
        """Validate ranges."""
        if self.brightness is not None and not 0 <= self.brightness <= 100:
            msg = f"Brightness must be 0-100, got {self.brightness}"
            raise ValueError(msg)
        if self.volume is not None and not 0 <= self.volume <= 100:
            msg = f"Volume must be 0-100, got {self.volume}"
            raise ValueError(msg)


@dataclass
class MonitorSummary(DataClassDictMixin):
    """Monitor summary from REST API `/api/v1/monitors` or WebSocket `monitors.list`.

    Based on MonitorSnapshot.to_summary() from netlink-webserver.

    Attributes
    ----------
        id: Monitor index in list
        bus: Monitor I2C bus ID
        model: Monitor model name
        type: Device type

    """

    id: int
    bus: int | str
    model: str
    type: str
