"""Tests for pynetlink main client."""

# pylint: disable=protected-access
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from aiohttp import ClientSession
from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT
from aresponses import ResponsesMockServer

from pynetlink import NetlinkClient

from . import load_fixtures


async def test_client_context_manager() -> None:
    """Test NetlinkClient as async context manager."""
    async with (
        ClientSession() as session,
        NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        ) as client,
    ):
        assert client.host == "192.168.1.100"
        assert client.token == "test-token"
        assert client.connected is False


async def test_client_connect_disconnect() -> None:
    """Test WebSocket connection lifecycle."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    with (
        patch.object(client._ws, "connect", new_callable=AsyncMock) as mock_connect,
        patch.object(
            client._ws, "disconnect", new_callable=AsyncMock
        ) as mock_disconnect,
        patch.object(client._rest, "close", new_callable=AsyncMock) as mock_close,
    ):
        await client.connect()
        mock_connect.assert_called_once()

        await client.disconnect()
        mock_disconnect.assert_called_once()
        mock_close.assert_called_once()


async def test_client_connected_property() -> None:
    """Test connected property delegates to WebSocket."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    # Initially not connected
    assert client.connected is False

    # Mock WebSocket as connected
    client._ws._connected = True
    assert client.connected is True


async def test_client_on_event_decorator() -> None:
    """Test event subscription decorator."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    callback_called = False

    @client.on("desk.state")
    async def handler(_data: dict) -> None:
        nonlocal callback_called
        callback_called = True

    # Verify it delegates to WebSocket
    assert "desk.state" in client._ws._callbacks


async def test_client_desk_state_property() -> None:
    """Test desk_state property returns cached state."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    # Initially None
    assert client.desk_state is None

    desk_data = load_fixtures("desk_state.json")
    await client._on_desk_state(desk_data)

    # Should return cached state
    assert client.desk_state is not None
    assert client.desk_state.height == 75.0


async def test_client_monitors_property() -> None:
    """Test monitors property returns cached monitor states."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    # Initially empty
    assert len(client.monitors) == 0

    monitor_data = load_fixtures("monitor_state.json")
    await client._on_monitor_state(monitor_data)

    # Should return cached state
    assert len(client.monitors) == 1
    assert "20" in client.monitors
    assert client.monitors["20"].brightness == 72


async def test_client_on_desk_state_nested_data() -> None:
    """Test _on_desk_state extracts nested data structure."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    # Test with nested data structure
    nested_data = {
        "data": {
            "height": 100.0,
            "mode": "moving_up",
            "moving": True,
        }
    }

    await client._on_desk_state(nested_data)

    assert client.desk_state is not None
    assert client.desk_state.height == 100.0
    assert client.desk_state.mode == "moving_up"


async def test_client_on_monitor_state_uses_string_key() -> None:
    """Test _on_monitor_state uses string bus_id as key."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    monitor_data = {
        "bus": 20,
        "power": "on",
        "brightness": 50,
    }

    await client._on_monitor_state(monitor_data)

    # Should use string key "20"
    assert "20" in client.monitors
    assert client.monitors["20"].bus == 20


async def test_client_get_desk_status(aresponses: ResponsesMockServer) -> None:
    """Test get_desk_status delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/status",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("desk_status_rest.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        status = await client.get_desk_status()
        assert status.height == 95.0


async def test_client_set_desk_height(aresponses: ResponsesMockServer) -> None:
    """Test set_desk_height delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/height",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("desk_set_height_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.set_desk_height(120.0)


async def test_client_stop_desk(aresponses: ResponsesMockServer) -> None:
    """Test stop_desk delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/stop",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.stop_desk()


async def test_client_stop_desk_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test stop_desk with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/stop",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.stop_desk(transport="rest")


async def test_client_stop_desk_auto_prefers_websocket() -> None:
    """Test stop_desk auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.stop_desk()
        mock_send.assert_called_once_with("command.desk.stop")


async def test_client_reset_desk(aresponses: ResponsesMockServer) -> None:
    """Test reset_desk delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/reset",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.reset_desk()


async def test_client_reset_desk_auto_websocket() -> None:
    """Test reset_desk auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.reset_desk()
        mock_send.assert_called_once_with("command.desk.reset")


async def test_client_reset_desk_websocket_transport() -> None:
    """Test reset_desk with explicit WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.reset_desk(transport="websocket")
        mock_send.assert_called_once_with("command.desk.reset")


async def test_client_reset_desk_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test reset_desk with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/reset",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.reset_desk(transport="rest")


async def test_client_calibrate_desk(aresponses: ResponsesMockServer) -> None:
    """Test calibrate_desk delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/calibrate",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.calibrate_desk()


async def test_client_calibrate_desk_auto_websocket() -> None:
    """Test calibrate_desk auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.calibrate_desk()
        mock_send.assert_called_once_with("command.desk.calibrate")


async def test_client_calibrate_desk_websocket_transport() -> None:
    """Test calibrate_desk with explicit WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.calibrate_desk(transport="websocket")
        mock_send.assert_called_once_with("command.desk.calibrate")


async def test_client_calibrate_desk_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test calibrate_desk with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/calibrate",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.calibrate_desk(transport="rest")


async def test_client_beep_desk(aresponses: ResponsesMockServer) -> None:
    """Test beep_desk delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/beep",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.beep_desk(count=3)


async def test_client_get_monitors(aresponses: ResponsesMockServer) -> None:
    """Test get_monitors delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitors",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("monitors_list_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        monitors = await client.get_monitors()
        assert len(monitors) == 1


async def test_client_get_monitor_status(aresponses: ResponsesMockServer) -> None:
    """Test get_monitor_status delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/status",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("monitor_state.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        status = await client.get_monitor_status(bus_id=20)
        assert status.brightness == 72


async def test_client_set_monitor_power(aresponses: ResponsesMockServer) -> None:
    """Test set_monitor_power delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/power",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.set_monitor_power(bus_id=20, state="on")


async def test_client_set_monitor_power_auto_websocket() -> None:
    """Test set_monitor_power auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_power(bus_id=1, state="off")
        mock_send.assert_called_once_with(
            "command.monitor.power",
            {"bus": "1", "state": "off"},
        )


async def test_client_set_monitor_power_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test set_monitor_power with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/power",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.set_monitor_power(bus_id=20, state="on", transport="rest")


async def test_client_set_monitor_brightness(aresponses: ResponsesMockServer) -> None:
    """Test set_monitor_brightness delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/brightness",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.set_monitor_brightness(bus_id=20, brightness=80)


async def test_client_set_monitor_brightness_websocket_transport() -> None:
    """Test set_monitor_brightness with explicit WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_brightness(
            bus_id=2,
            brightness=70,
            transport="websocket",
        )
        mock_send.assert_called_once_with(
            "command.monitor.brightness",
            {"bus": "2", "brightness": 70},
        )


async def test_client_set_monitor_brightness_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test set_monitor_brightness with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/brightness",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.set_monitor_brightness(
            bus_id=20,
            brightness=80,
            transport="rest",
        )


async def test_client_set_monitor_volume(aresponses: ResponsesMockServer) -> None:
    """Test set_monitor_volume delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/volume",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.set_monitor_volume(bus_id=20, volume=50)


async def test_client_set_monitor_volume_auto_websocket() -> None:
    """Test set_monitor_volume auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_volume(bus_id=3, volume=30)
        mock_send.assert_called_once_with(
            "command.monitor.volume",
            {"bus": "3", "volume": 30},
        )


async def test_client_set_monitor_volume_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test set_monitor_volume with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/volume",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.set_monitor_volume(bus_id=20, volume=50, transport="rest")


async def test_client_set_monitor_volume_websocket() -> None:
    """Test set_monitor_volume with WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_volume(
            bus_id=1,
            volume=40,
            transport="websocket",
        )
        mock_send.assert_called_once_with(
            "command.monitor.volume",
            {"bus": "1", "volume": 40},
        )


async def test_client_set_monitor_source(aresponses: ResponsesMockServer) -> None:
    """Test set_monitor_source delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/source",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.set_monitor_source(bus_id=20, source="HDMI1")


async def test_client_set_monitor_source_auto_websocket() -> None:
    """Test set_monitor_source auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_source(bus_id=4, source="DP")
        mock_send.assert_called_once_with(
            "command.monitor.source",
            {"bus": "4", "source": "DP"},
        )


async def test_client_set_monitor_source_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test set_monitor_source with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/source",
        METH_PUT,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.set_monitor_source(bus_id=20, source="HDMI1", transport="rest")


async def test_client_get_browser_url(aresponses: ResponsesMockServer) -> None:
    """Test get_browser_url delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/browser/url",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("browser_url_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        url = await client.get_browser_url()
        assert url == "https://example.com"


async def test_client_set_browser_url(aresponses: ResponsesMockServer) -> None:
    """Test set_browser_url delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/browser/url",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.set_browser_url("https://example.com")


async def test_client_set_browser_url_auto_websocket() -> None:
    """Test set_browser_url auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_browser_url("https://example.com/dashboard")
        mock_send.assert_called_once_with(
            "command.browser.url",
            {"url": "https://example.com/dashboard"},
        )


async def test_client_set_browser_url_websocket_transport() -> None:
    """Test set_browser_url with explicit WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_browser_url(
            "https://example.com/app",
            transport="websocket",
        )
        mock_send.assert_called_once_with(
            "command.browser.url",
            {"url": "https://example.com/app"},
        )


async def test_client_set_browser_url_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test set_browser_url with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/browser/url",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.set_browser_url(
            "https://example.com/app",
            transport="rest",
        )


async def test_client_refresh_browser(aresponses: ResponsesMockServer) -> None:
    """Test refresh_browser delegates to REST."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/browser/refresh",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        await client.refresh_browser()


async def test_client_refresh_browser_auto_websocket() -> None:
    """Test refresh_browser auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.refresh_browser()
        mock_send.assert_called_once_with("command.browser.refresh")


async def test_client_refresh_browser_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test refresh_browser with explicit REST transport."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/browser/refresh",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session
        client._ws._connected = True

        await client.refresh_browser(transport="rest")


async def test_client_session_management_with_own_session() -> None:
    """Test that client doesn't close user-provided session."""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.close = AsyncMock()

    client = NetlinkClient(
        host="192.168.1.100",
        token="test-token",
        session=mock_session,
    )

    with (
        patch.object(client._ws, "disconnect", new_callable=AsyncMock),
        patch.object(client._rest, "close", new_callable=AsyncMock),
    ):
        await client.disconnect()

    # Session should NOT be closed because user provided it
    mock_session.close.assert_not_called()


async def test_client_session_management_creates_own_session() -> None:
    """Test that client closes self-created session."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    # Simulate REST creating its own session
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.close = AsyncMock()
    client.session = mock_session
    client._close_session = True

    with (
        patch.object(client._ws, "disconnect", new_callable=AsyncMock),
        patch.object(client._rest, "close", new_callable=AsyncMock),
    ):
        await client.disconnect()

    # Session SHOULD be closed because client created it
    mock_session.close.assert_called_once()


# WebSocket Commands (v0.2.0) - Transport Parameter Tests


async def test_client_set_desk_height_websocket_transport() -> None:
    """Test set_desk_height with WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    # Mock WebSocket as connected
    client._ws._connected = True
    client._ws._sio = AsyncMock()
    client._ws._sio.emit = AsyncMock()

    # Mock send_command
    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        result = await client.set_desk_height(120.0, transport="websocket")

        # Should use WebSocket
        mock_send.assert_called_once_with("command.desk.height", {"height": 120.0})
        assert result == {"status": "ok"}


async def test_client_set_desk_height_rest_transport(
    aresponses: ResponsesMockServer,
) -> None:
    """Test set_desk_height with REST transport (forced)."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/height",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("desk_set_height_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        # Mock WebSocket as connected
        client._ws._connected = True

        # Even though WebSocket is connected, should use REST
        result = await client.set_desk_height(120.0, transport="rest")
        assert result["status"] == "ok"


async def test_client_set_desk_height_auto_uses_websocket() -> None:
    """Test set_desk_height with auto transport uses WebSocket when connected."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")

    # Mock WebSocket as connected
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_ws:
        # Auto mode with WebSocket connected should use WebSocket
        await client.set_desk_height(120.0)  # transport="auto" is default

        mock_ws.assert_called_once_with("command.desk.height", {"height": 120.0})


async def test_client_set_desk_height_auto_fallback_rest(
    aresponses: ResponsesMockServer,
) -> None:
    """Auto transport falls back to REST when WebSocket is not connected."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/height",
        METH_POST,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("desk_set_height_response.json"),
        ),
    )

    async with ClientSession() as session:
        client = NetlinkClient(
            host="192.168.1.100",
            token="test-token",
            session=session,
        )
        client._rest._session = session

        # WebSocket NOT connected
        client._ws._connected = False

        # Auto mode without WebSocket should use REST
        result = await client.set_desk_height(120.0)  # transport="auto" is default
        assert result["status"] == "ok"


async def test_client_stop_desk_websocket() -> None:
    """Test stop_desk with WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.stop_desk(transport="websocket")
        mock_send.assert_called_once_with("command.desk.stop")


async def test_client_set_monitor_power_websocket() -> None:
    """Test set_monitor_power with WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_power(bus_id=0, state="on", transport="websocket")
        mock_send.assert_called_once_with(
            "command.monitor.power",
            {"bus": "0", "state": "on"},
        )


async def test_client_set_monitor_brightness_auto() -> None:
    """Test set_monitor_brightness with auto transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_brightness(bus_id=0, brightness=80)
        mock_send.assert_called_once_with(
            "command.monitor.brightness",
            {"bus": "0", "brightness": 80},
        )


async def test_client_set_monitor_source_websocket() -> None:
    """Test set_monitor_source with WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.set_monitor_source(
            bus_id=2,
            source="USBC",
            transport="websocket",
        )
        mock_send.assert_called_once_with(
            "command.monitor.source",
            {"bus": "2", "source": "USBC"},
        )


async def test_client_refresh_browser_websocket() -> None:
    """Test refresh_browser with WebSocket transport."""
    client = NetlinkClient(host="192.168.1.100", token="test-token")
    client._ws._connected = True

    with patch.object(
        client._ws,
        "send_command",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ) as mock_send:
        await client.refresh_browser(transport="websocket")
        mock_send.assert_called_once_with("command.browser.refresh")
