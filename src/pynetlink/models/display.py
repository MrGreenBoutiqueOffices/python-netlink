"""Display data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mashumaro import DataClassDictMixin
from mashumaro.exceptions import InvalidFieldValue, MissingField

from pynetlink.exceptions import NetlinkDataError


@dataclass
class DisplayState(DataClassDictMixin):
    """Current state values of a display (nested in Display).

    Attributes
    ----------
        power: Current power state ("on", "off")
        source: Current input source (e.g., "HDMI1", "USBC")
        brightness: Current brightness level (0-100)
        volume: Current volume level (0-100)
        error: Error message if any

    """

    power: str | None = None
    source: str | None = None
    brightness: int | None = None
    volume: int | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        """Validate ranges."""
        if self.brightness is not None and not 0 <= self.brightness <= 100:
            msg = f"Brightness must be 0-100, got {self.brightness}"
            raise ValueError(msg)
        if self.volume is not None and not 0 <= self.volume <= 100:
            msg = f"Volume must be 0-100, got {self.volume}"
            raise ValueError(msg)


@dataclass
class Display(DataClassDictMixin):
    """Full display information from WebSocket `display.state` event or REST API.

    Attributes
    ----------
        bus: Display I2C bus ID (can be int or str)
        model: Display model name
        type: Device type ("display", "tablet")
        supports: Display capabilities dict (e.g., {"power": True, "source": True})
        state: Nested current state values (power, source, brightness, volume, error)
        serial_number: Serial number if available
        source_options: List of available input sources if supported

    """

    bus: int | str
    model: str
    type: str
    supports: dict[str, Any]
    state: DisplayState
    serial_number: str | None = None
    source_options: list[str] | None = None

    def __post_init__(self) -> None:
        """Convert state dict to DisplayState if needed."""
        if isinstance(self.state, dict):
            try:
                object.__setattr__(self, "state", DisplayState.from_dict(self.state))
            except (MissingField, InvalidFieldValue) as exc:
                msg = f"Incomplete or invalid display state data: {exc}"
                raise NetlinkDataError(msg) from exc


@dataclass
class DisplaySummary(DataClassDictMixin):
    """Display summary from REST API `/api/v1/displays` or WebSocket `displays.list`.

    Based on DisplaySnapshot.to_summary() from netlink-webserver.

    Attributes
    ----------
        id: Display index in list
        bus: Display I2C bus ID
        model: Display model name
        type: Device type

    """

    id: int
    bus: int | str
    model: str
    type: str
