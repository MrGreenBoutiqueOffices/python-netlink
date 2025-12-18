"""Tests for pynetlink data models."""

from __future__ import annotations

import json

import pytest
from syrupy.assertion import SnapshotAssertion

from pynetlink.models import (
    BrowserState,
    DeskState,
    DeskStatus,
    MonitorState,
    NetlinkDevice,
    SystemInfo,
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
    assert desk_state.capabilities is not None
    assert desk_state.inventory is not None

    # Snapshot test for serialization
    assert desk_state.to_dict() == snapshot


def test_desk_state_validation() -> None:
    """Test DeskState validation."""
    # Valid height range
    valid_state = DeskState(
        height=75.0,
        mode="idle",
        moving=False,
    )
    assert valid_state.height == 75.0

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


def test_desk_status_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test DeskStatus deserialization from REST API."""
    data = json.loads(load_fixtures("desk_status_rest.json"))
    desk_status = DeskStatus.from_dict(data)

    assert desk_status.height == 95.0
    assert desk_status.mode == "stopped"
    assert desk_status.moving is False
    assert desk_status.error is None
    assert desk_status.controller_connected is True

    # Snapshot test
    assert desk_status.to_dict() == snapshot


def test_monitor_state_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test MonitorState deserialization from WebSocket data."""
    data = json.loads(load_fixtures("monitor_state.json"))
    monitor_state = MonitorState.from_dict(data)

    assert monitor_state.bus == 20
    assert monitor_state.power == "on"
    assert monitor_state.source == "HDMI1"
    assert monitor_state.brightness == 72
    assert monitor_state.volume == 50
    assert monitor_state.model == "Dell U2723QE"
    assert monitor_state.type == "monitor"
    assert monitor_state.sn == "ABC123XYZ"
    assert monitor_state.supports is not None
    assert monitor_state.source_options is not None

    # Snapshot test
    assert monitor_state.to_dict() == snapshot


def test_monitor_state_validation() -> None:
    """Test MonitorState brightness and volume validation."""
    # Valid brightness and volume
    valid_state = MonitorState(
        bus=20,
        power="on",
        brightness=50,
        volume=50,
    )
    assert valid_state.brightness == 50
    assert valid_state.volume == 50

    # Invalid brightness - too low
    with pytest.raises(ValueError, match="Brightness must be 0-100"):
        MonitorState(
            bus=20,
            power="on",
            brightness=-10,
        )

    # Invalid brightness - too high
    with pytest.raises(ValueError, match="Brightness must be 0-100"):
        MonitorState(
            bus=20,
            power="on",
            brightness=150,
        )

    # Invalid volume - too low
    with pytest.raises(ValueError, match="Volume must be 0-100"):
        MonitorState(
            bus=20,
            power="on",
            volume=-5,
        )

    # Invalid volume - too high
    with pytest.raises(ValueError, match="Volume must be 0-100"):
        MonitorState(
            bus=20,
            power="on",
            volume=110,
        )


def test_monitor_state_bus_int_or_str() -> None:
    """Test MonitorState accepts both int and str for bus_id."""
    # Bus as int
    state_int = MonitorState(bus=20, power="on")
    assert state_int.bus == 20

    # Bus as str
    state_str = MonitorState(bus="20", power="on")
    assert state_str.bus == "20"


def test_browser_state_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test BrowserState deserialization."""
    data = json.loads(load_fixtures("browser_state.json"))
    browser_state = BrowserState.from_dict(data)

    assert browser_state.url == "https://example.com"

    # Snapshot test
    assert browser_state.to_dict() == snapshot


def test_system_info_from_dict(snapshot: SnapshotAssertion) -> None:
    """Test SystemInfo deserialization."""
    data = json.loads(load_fixtures("system_info.json"))
    system_info = SystemInfo.from_dict(data)

    assert system_info.version == "1.2.3"
    assert system_info.api_version == "1.0"
    assert system_info.device_id == "abc123def456"
    assert system_info.device_name == "Office Desk 1"
    assert system_info.uptime == 86400

    # Snapshot test
    assert system_info.to_dict() == snapshot


def test_netlink_device_from_zeroconf() -> None:
    """Test NetlinkDevice creation from Zeroconf data."""
    device = NetlinkDevice(
        name="Office Desk 1",
        host="192.168.1.100",
        port=80,
        device_id="abc123",
        model="netlink-v2",
        version="1.2.3",
        api_version="1.0",
        has_desk=True,
        monitors=["20", "21"],
        ws_path="/socket.io",
    )

    assert device.name == "Office Desk 1"
    assert device.host == "192.168.1.100"
    assert device.port == 80
    assert device.device_id == "abc123"
    assert device.model == "netlink-v2"
    assert device.version == "1.2.3"
    assert device.api_version == "1.0"
    assert device.has_desk is True
    assert device.monitors == ["20", "21"]
    assert device.ws_path == "/socket.io"


def test_desk_state_optional_fields() -> None:
    """Test DeskState with minimal required fields."""
    desk_state = DeskState(
        height=75.0,
        mode="idle",
        moving=False,
    )

    assert desk_state.height == 75.0
    assert desk_state.mode == "idle"
    assert desk_state.moving is False
    assert desk_state.error is None
    assert desk_state.target is None
    assert desk_state.capabilities is None
    assert desk_state.inventory is None


def test_monitor_state_optional_fields() -> None:
    """Test MonitorState with minimal required fields."""
    monitor_state = MonitorState(
        bus=20,
        power="on",
    )

    assert monitor_state.bus == 20
    assert monitor_state.power == "on"
    assert monitor_state.source is None
    assert monitor_state.brightness is None
    assert monitor_state.volume is None
    assert monitor_state.model is None
    assert monitor_state.type is None
    assert monitor_state.sn is None
    assert monitor_state.supports is None
    assert monitor_state.source_options is None
