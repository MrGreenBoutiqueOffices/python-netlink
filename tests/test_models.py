"""Tests for pynetlink data models."""

from __future__ import annotations

import json
from dataclasses import asdict

from syrupy.assertion import SnapshotAssertion

from pynetlink.models import (
    BrowserState,
    Desk,
    DeskState,
    DeviceInfo,
    Display,
    DisplayState,
    NetlinkDevice,
)

from . import load_fixtures


def test_desk_state_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test DeskState deserialization from WebSocket data."""
    data = json.loads(load_fixtures("desk_state.json"))
    desk_state = DeskState.from_dict(data)

    assert desk_state.height == 75.0
    assert desk_state.mode == "idle"
    assert desk_state.moving is False
    assert desk_state.error is None
    assert desk_state.target is None

    # Snapshot test for serialization
    assert desk_state.to_dict() == snapshot


def test_desk_state_validation(snapshot: SnapshotAssertion) -> None:
    """Test DeskState with valid height range."""
    valid_state = DeskState(
        height=75.0,
        mode="idle",
        moving=False,
    )
    assert valid_state.height == 75.0
    assert valid_state.to_dict() == snapshot


def test_desk_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test Desk deserialization from REST API."""
    data = json.loads(load_fixtures("desk_status_rest.json"))
    desk = Desk.from_dict(data)

    assert desk.state.height == 95.0
    assert desk.state.mode == "stopped"
    assert desk.state.moving is False
    assert desk.state.error is None
    assert desk.state.target == 110.0
    assert desk.state.beep == "on"
    assert desk.capabilities is not None
    assert desk.inventory is not None

    # Snapshot test
    assert desk.to_dict() == snapshot


def test_display_state_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test Display deserialization from WebSocket data."""
    data = json.loads(load_fixtures("display_state.json"))
    display_state = Display.from_dict(data)

    assert display_state.bus == 20
    assert display_state.state.power == "on"
    assert display_state.state.source == "HDMI1"
    assert display_state.state.brightness == 72
    assert display_state.state.volume == 50
    assert display_state.model == "Dell U2723QE"
    assert display_state.type == "monitor"
    assert display_state.serial_number == "ABC123XYZ"
    assert display_state.supports is not None
    assert display_state.source_options is not None

    # Snapshot test
    assert display_state.to_dict() == snapshot


def test_display_state_validation(snapshot: SnapshotAssertion) -> None:
    """Test DisplayState with valid brightness and volume."""
    valid_state = DisplayState(
        power="on",
        brightness=50,
        volume=50,
    )
    assert valid_state.brightness == 50
    assert valid_state.volume == 50
    assert valid_state.to_dict() == snapshot


def test_display_state_bus_int_or_str(snapshot: SnapshotAssertion) -> None:
    """Test Display accepts both int and str for bus_id."""
    # Bus as int
    state_int = Display(
        bus=20,
        model="Test",
        type="monitor",
        supports={},
        state=DisplayState(power="on"),
    )
    assert state_int.bus == 20

    # Bus as str
    state_str = Display(
        bus="20",
        model="Test",
        type="monitor",
        supports={},
        state=DisplayState(power="on"),
    )
    assert state_str.bus == "20"
    assert {"int": state_int.to_dict(), "str": state_str.to_dict()} == snapshot


def test_browser_state_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test BrowserState deserialization."""
    data = json.loads(load_fixtures("browser_state.json"))
    browser_state = BrowserState.from_dict(data)

    assert browser_state.url == "https://example.com"

    # Snapshot test
    assert browser_state.to_dict() == snapshot


def test_device_info_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test DeviceInfo deserialization."""
    data = json.loads(load_fixtures("device_info.json"))
    device_info = DeviceInfo.from_dict(data)

    assert device_info.version == "1.2.3"
    assert device_info.api_version == "1.0"
    assert device_info.device_id == "abc123def456"
    assert device_info.device_name == "Office Desk 1"
    assert device_info.model == "NetOS Desk"

    # Snapshot test
    assert device_info.to_dict() == snapshot


def test_netlink_device_from_zeroconf(snapshot: SnapshotAssertion) -> None:
    """Test NetlinkDevice creation from Zeroconf data."""
    device = NetlinkDevice(
        host="192.168.1.100",
        port=80,
        device_id="abc123",
        device_name="Office Desk 1",
        model="netlink-v2",
        version="1.2.3",
        api_version="1.0",
        has_desk=True,
        displays=["20", "21"],
        ws_path="/socket.io",
    )

    assert device.host == "192.168.1.100"
    assert device.port == 80
    assert device.device_id == "abc123"
    assert device.device_name == "Office Desk 1"
    assert device.model == "netlink-v2"
    assert device.version == "1.2.3"
    assert device.api_version == "1.0"
    assert device.has_desk is True
    assert device.displays == ["20", "21"]
    assert device.ws_path == "/socket.io"
    assert asdict(device) == snapshot


def test_desk_state_optional_fields(snapshot: SnapshotAssertion) -> None:
    """Test DeskState with minimal required fields."""
    desk_state = DeskState(
        height=75.0,
        mode="idle",
        moving=False,
    )

    assert desk_state.height == 75.0
    assert desk_state.mode == "idle"
    assert desk_state.moving is False
    assert desk_state.to_dict() == snapshot
    assert desk_state.error is None
    assert desk_state.target is None


def test_display_state_optional_fields() -> None:
    """Test Display with minimal required fields."""
    display_state = Display(
        bus=20,
        model="Test",
        type="monitor",
        supports={},
        state=DisplayState(power="on"),
    )

    assert display_state.bus == 20
    assert display_state.state.power == "on"
    assert display_state.state.source is None
    assert display_state.state.brightness is None
    assert display_state.state.volume is None
    assert display_state.model == "Test"
    assert display_state.type == "monitor"
    assert display_state.serial_number is None
    assert not display_state.supports
    assert display_state.source_options is None


def test_state_dict_conversion() -> None:
    """Test Desk and Display convert dict state to typed state in __post_init__."""
    # Test Desk converts dict to DeskState
    desk = Desk(
        capabilities={},
        inventory={},
        state={"height": 75.0, "mode": "idle", "moving": False},  # type: ignore[arg-type]
    )
    assert isinstance(desk.state, DeskState)
    assert desk.state.height == 75.0
    assert desk.state.mode == "idle"
    assert desk.state.moving is False

    # Test Display converts dict to DisplayState
    display = Display(
        bus=20,
        model="Test",
        type="monitor",
        supports={},
        state={"power": "on", "brightness": 75},  # type: ignore[arg-type]
    )
    assert isinstance(display.state, DisplayState)
    assert display.state.power == "on"
    assert display.state.brightness == 75
