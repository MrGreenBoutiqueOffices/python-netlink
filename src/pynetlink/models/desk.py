"""Desk data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mashumaro import DataClassDictMixin
from mashumaro.exceptions import InvalidFieldValue, MissingField

from pynetlink.exceptions import NetlinkDataError


@dataclass
class DeskState(DataClassDictMixin):
    """Current state values of a desk (nested in Desk).

    Attributes
    ----------
        height: Current height in cm
        mode: Current operation mode (e.g., "idle", "moving")
        moving: Whether desk is currently moving
        error: Error message if any (optional)
        target: Target height if moving, None otherwise
        beep: Beep setting ("on" or "off", may be present in some events)

    """

    height: float
    mode: str
    moving: bool
    error: str | None = None
    target: float | None = None
    beep: str | None = None

    def __post_init__(self) -> None:
        """Validate height range."""
        if not 60.0 <= self.height <= 130.0:
            msg = f"Height must be between 60 and 130 cm, got {self.height}"
            raise ValueError(msg)


@dataclass
class Desk(DataClassDictMixin):
    """Full desk information from WebSocket `desk.state` event or REST API.

    Attributes
    ----------
        capabilities: Desk capabilities dict (supports + attributes)
        inventory: Desk inventory metadata
        state: Nested current state values (height, mode, moving, target, beep, error)

    """

    capabilities: dict[str, Any]
    inventory: dict[str, Any]
    state: DeskState

    def __post_init__(self) -> None:
        """Convert state dict to DeskState if needed."""
        if isinstance(self.state, dict):
            try:
                object.__setattr__(self, "state", DeskState.from_dict(self.state))
            except (MissingField, InvalidFieldValue) as exc:
                msg = f"Incomplete or invalid desk state data: {exc}"
                raise NetlinkDataError(msg) from exc
