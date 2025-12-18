"""Desk data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mashumaro import DataClassDictMixin


@dataclass
class DeskState(DataClassDictMixin):
    """Real-time desk state from WebSocket `desk.state` event.

    Based on DeskSnapshot TypedDict from netlink-webserver.

    Attributes
    ----------
        height: Current height in cm
        mode: Current operation mode (e.g., "idle", "moving")
        moving: Whether desk is currently moving
        error: Error message if any (optional)
        target: Target height if moving, None otherwise
        beep: Beep setting ("on" or "off", may be present in some events)
        capabilities: Desk capabilities (optional)
        inventory: Desk inventory info (optional)

    """

    height: float
    mode: str
    moving: bool
    error: str | None = None
    target: float | None = None
    beep: str | None = None
    capabilities: dict[str, Any] | None = None
    inventory: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate height range."""
        if not 60.0 <= self.height <= 130.0:
            msg = f"Height must be between 60 and 130 cm, got {self.height}"
            raise ValueError(msg)


@dataclass
class DeskStatus(DataClassDictMixin):
    """Full desk status from REST API `/api/v1/desk/status`.

    Based on DeskStatus Pydantic model from netlink-webserver.

    Attributes
    ----------
        height: Current height in cm
        mode: Current operation mode
        moving: Whether desk is currently moving
        error: Error message if any
        controller_connected: Whether desk controller is connected

    """

    height: float
    mode: str
    moving: bool
    error: str | None = None
    controller_connected: bool | None = None
