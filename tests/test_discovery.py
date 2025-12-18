"""Tests for pynetlink device discovery."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

from pynetlink import NetlinkClient
from pynetlink.models import NetlinkDevice


async def test_discover_devices() -> None:
    """Test device discovery via mDNS/Zeroconf."""
    # Mock Zeroconf service info
    mock_service_info = MagicMock()
    mock_service_info.parsed_addresses.return_value = ["192.168.1.100"]
    mock_service_info.port = 80
    mock_service_info.name = "Netlink Device._netlink._tcp.local."
    mock_service_info.properties = {
        b"version": b"1.0.0",
        b"model": b"netlink-v1",
    }

    with (
        patch("pynetlink.netlink.Zeroconf") as mock_zeroconf_class,
        patch("pynetlink.netlink.ServiceBrowser") as mock_browser_class,
    ):
        # Mock Zeroconf instance
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        mock_zc.get_service_info.return_value = mock_service_info

        # Capture the listener passed to ServiceBrowser
        captured_listener = None

        def capture_browser(_zc: Any, _service_type: Any, listener: Any) -> MagicMock:
            nonlocal captured_listener
            captured_listener = listener
            return MagicMock()

        mock_browser_class.side_effect = capture_browser

        # Start discovery
        discovery_task = asyncio.create_task(
            NetlinkClient.discover_devices(discovery_timeout=0.1)
        )

        # Give it a moment to set up
        await asyncio.sleep(0.05)

        # Simulate service discovery
        if captured_listener:
            captured_listener.add_service(
                mock_zc, "_netlink._tcp.local.", "test-device"
            )
            # Exercise no-op remove/update handlers for coverage
            captured_listener.remove_service(
                mock_zc, "_netlink._tcp.local.", "test-device"
            )
            captured_listener.update_service(
                mock_zc, "_netlink._tcp.local.", "test-device"
            )

        # Wait for discovery to complete
        devices = await discovery_task

        # Verify device was discovered
        assert len(devices) == 1
        assert devices[0].host == "192.168.1.100"
        assert devices[0].port == 80

        # Verify Zeroconf was closed
        mock_zc.close.assert_called_once()


async def test_netlink_device_from_service_info() -> None:
    """Test NetlinkDevice.from_service_info method."""
    mock_service_info = MagicMock()
    mock_service_info.parsed_addresses.return_value = ["192.168.1.100"]
    mock_service_info.port = 80
    mock_service_info.name = "Office Netlink._netlink._tcp.local."
    mock_service_info.properties = {
        b"name": b"Office Netlink",
        b"version": b"2.0.0",
        b"model": b"netlink-pro",
        b"device_id": b"abc123",
        b"has_desk": b"true",
        b"monitors": b"20,21",
    }

    device = NetlinkDevice.from_service_info(mock_service_info)

    assert device.host == "192.168.1.100"
    assert device.port == 80
    assert device.name == "Office Netlink"
    assert device.version == "2.0.0"
    assert device.model == "netlink-pro"
    assert device.device_id == "abc123"
    assert device.has_desk is True
    assert device.monitors == ["20", "21"]


async def test_netlink_device_from_service_info_with_ipv6() -> None:
    """Test NetlinkDevice.from_service_info with IPv6 address."""
    mock_service_info = MagicMock()
    mock_service_info.parsed_addresses.return_value = ["fe80::1"]
    mock_service_info.port = 8080
    mock_service_info.name = "Device._netlink._tcp.local."
    mock_service_info.properties = {
        b"version": b"1.5.0",
    }

    device = NetlinkDevice.from_service_info(mock_service_info)

    assert device.host == "fe80::1"
    assert device.port == 8080


async def test_netlink_device_from_service_info_missing_properties() -> None:
    """Test NetlinkDevice.from_service_info when properties are empty."""
    mock_service_info = MagicMock()
    mock_service_info.parsed_addresses.return_value = []
    mock_service_info.port = 443
    mock_service_info.properties = {}
    mock_service_info.name = "Minimal._netlink._tcp.local."

    device = NetlinkDevice.from_service_info(mock_service_info)

    assert device.name == "Unknown"
    assert device.host == ""  # No parsed addresses
    assert not device.monitors
    assert device.ws_path == "/socket.io"


async def test_discover_devices_ignores_missing_service_info() -> None:
    """Ensure discovery ignores services without ServiceInfo."""
    with (
        patch("pynetlink.netlink.Zeroconf") as mock_zeroconf_class,
        patch("pynetlink.netlink.ServiceBrowser") as mock_browser_class,
    ):
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        mock_zc.get_service_info.return_value = None  # Simulate missing info

        captured_listener = None

        def capture_browser(_zc: Any, _service_type: Any, listener: Any) -> MagicMock:
            nonlocal captured_listener
            captured_listener = listener
            return MagicMock()

        mock_browser_class.side_effect = capture_browser

        discovery_task = asyncio.create_task(
            NetlinkClient.discover_devices(discovery_timeout=0.05)
        )

        await asyncio.sleep(0.01)

        if captured_listener:
            captured_listener.add_service(mock_zc, "_netlink._tcp.local.", "no-info")

        devices = await discovery_task

        assert devices == []
