"""Tests for pynetlink exception handling."""

from __future__ import annotations

import pytest

from pynetlink.exceptions import NetlinkDataError
from pynetlink.models import Desk, DeskState, Display, DisplayState


def test_desk_invalid_state_raises_netlink_data_error() -> None:
    """Test Desk raises NetlinkDataError when state dict is invalid."""
    # Missing required fields
    with pytest.raises(NetlinkDataError, match="Incomplete or invalid desk state data"):
        Desk(
            capabilities={},
            inventory={},
            state={"height": 75.0},  # type: ignore[arg-type]  # Missing mode and moving
        )

    # Invalid field types
    with pytest.raises(NetlinkDataError, match="Incomplete or invalid desk state data"):
        Desk(
            capabilities={},
            inventory={},
            state={"height": "not-a-number", "mode": "idle", "moving": False},  # type: ignore[arg-type]
        )


def test_display_invalid_state_raises_netlink_data_error() -> None:
    """Test Display raises NetlinkDataError when state dict has invalid types."""
    # Invalid field type that mashumaro can't parse
    with pytest.raises(
        NetlinkDataError, match="Incomplete or invalid display state data"
    ):
        Display(
            bus=20,
            model="Test",
            type="monitor",
            supports={},
            state={"power": "on", "brightness": "not-a-number"},  # type: ignore[arg-type]  # Invalid type
        )


def test_desk_state_height_validation() -> None:
    """Test DeskState height range validation."""
    # Invalid height - too low
    with pytest.raises(ValueError, match="Height must be between"):
        DeskState(
            height=50.0,  # Below minimum
            mode="idle",
            moving=False,
        )

    # Invalid height - too high
    with pytest.raises(ValueError, match="Height must be between"):
        DeskState(
            height=150.0,  # Above maximum
            mode="idle",
            moving=False,
        )


def test_display_state_brightness_validation() -> None:
    """Test DisplayState brightness range validation."""
    # Invalid brightness - too low
    with pytest.raises(ValueError, match="Brightness must be 0-100"):
        DisplayState(
            power="on",
            brightness=-10,
        )

    # Invalid brightness - too high
    with pytest.raises(ValueError, match="Brightness must be 0-100"):
        DisplayState(
            power="on",
            brightness=150,
        )


def test_display_state_volume_validation() -> None:
    """Test DisplayState volume range validation."""
    # Invalid volume - too low
    with pytest.raises(ValueError, match="Volume must be 0-100"):
        DisplayState(
            power="on",
            volume=-5,
        )

    # Invalid volume - too high
    with pytest.raises(ValueError, match="Volume must be 0-100"):
        DisplayState(
            power="on",
            volume=110,
        )
