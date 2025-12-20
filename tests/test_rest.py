"""Tests for pynetlink REST API client."""

# pylint: disable=protected-access
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientError, ClientSession
from aiohttp.hdrs import METH_GET, METH_PATCH, METH_POST, METH_PUT
from aresponses import ResponsesMockServer

from pynetlink.exceptions import (
    NetlinkAuthenticationError,
    NetlinkConnectionError,
    NetlinkTimeoutError,
)
from pynetlink.rest import NetlinkREST

from . import load_fixtures


async def test_device_get_info(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/device/info."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/device/info",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("device_info.json"),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        info = await rest.get_device_info()

        assert info.device_id == "abc123def456"
        assert info.model == "NetOS Desk"


async def test_desk_get_status(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/desk/status."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        status = await rest.get_desk_status()

        assert status.height == 95.0
        assert status.mode == "stopped"
        assert status.moving is False
        assert status.controller_connected is True


async def test_desk_set_height(aresponses: ResponsesMockServer) -> None:
    """Test POST /api/v1/desk/height."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.set_desk_height(120.0)


async def test_desk_set_height_invalid_range() -> None:
    """Test desk height validation."""
    rest = NetlinkREST(host="192.168.1.100", token="test-token")

    # Too low
    with pytest.raises(ValueError, match="Height must be between"):
        await rest.set_desk_height(50.0)

    # Too high
    with pytest.raises(ValueError, match="Height must be between"):
        await rest.set_desk_height(150.0)


async def test_desk_stop(aresponses: ResponsesMockServer) -> None:
    """Test POST /api/v1/desk/stop."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.stop_desk()


async def test_desk_reset(aresponses: ResponsesMockServer) -> None:
    """Test POST /api/v1/desk/reset."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.reset_desk()


async def test_desk_calibrate(aresponses: ResponsesMockServer) -> None:
    """Test POST /api/v1/desk/calibrate."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.calibrate_desk()


async def test_desk_beep(aresponses: ResponsesMockServer) -> None:
    """Test POST /api/v1/desk/beep."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.beep_desk(count=3)


async def test_desk_beep_invalid_range() -> None:
    """Test beep_desk validation."""
    rest = NetlinkREST(host="192.168.1.100", token="test-token")

    with pytest.raises(ValueError, match="Beep count must be between"):
        await rest.beep_desk(count=0)

    with pytest.raises(ValueError, match="Beep count must be between"):
        await rest.beep_desk(count=6)


async def test_monitors_list(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/monitors."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        monitors = await rest.get_monitors()

        assert len(monitors) == 1
        assert monitors[0].id == 0
        assert monitors[0].bus == 20
        assert monitors[0].model == "Dell U2723QE"


async def test_monitors_list_wrapped(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/monitors when wrapped in dict."""
    monitors_payload = {
        "monitors": [
            {
                "id": 1,
                "bus": 30,
                "model": "LG UltraFine",
                "type": "monitor",
            }
        ]
    }

    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitors",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(monitors_payload),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        monitors = await rest.get_monitors()

        assert len(monitors) == 1
        assert monitors[0].id == 1
        assert monitors[0].bus == 30


async def test_monitor_get_status(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/monitor/{bus_id}/status."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        status = await rest.get_monitor_status(bus_id=20)

        assert status.bus == 20
        assert status.power == "on"
        assert status.brightness == 72


async def test_monitor_set_power(aresponses: ResponsesMockServer) -> None:
    """Test PUT /api/v1/monitor/{bus_id}/power."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.set_monitor_power(bus_id=20, state="on")


async def test_monitor_get_power(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/monitor/{bus_id}/power."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/power",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"state": "off"}),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        state = await rest.get_monitor_power(bus_id=20)

        assert state == "off"


async def test_monitor_set_brightness(aresponses: ResponsesMockServer) -> None:
    """Test PUT /api/v1/monitor/{bus_id}/brightness."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.set_monitor_brightness(bus_id=20, brightness=80)


async def test_monitor_set_brightness_invalid_range() -> None:
    """Test monitor brightness validation."""
    rest = NetlinkREST(host="192.168.1.100", token="test-token")

    # Too low
    with pytest.raises(ValueError, match="Brightness must be between"):
        await rest.set_monitor_brightness(bus_id=20, brightness=-10)

    # Too high
    with pytest.raises(ValueError, match="Brightness must be between"):
        await rest.set_monitor_brightness(bus_id=20, brightness=150)


async def test_monitor_get_brightness(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/monitor/{bus_id}/brightness."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/brightness",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"brightness": 65}),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        brightness = await rest.get_monitor_brightness(bus_id=20)

        assert brightness == 65


async def test_monitor_set_volume(aresponses: ResponsesMockServer) -> None:
    """Test PUT /api/v1/monitor/{bus_id}/volume."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.set_monitor_volume(bus_id=20, volume=50)


async def test_monitor_set_volume_invalid_range() -> None:
    """Test monitor volume validation."""
    rest = NetlinkREST(host="192.168.1.100", token="test-token")

    # Too low
    with pytest.raises(ValueError, match="Volume must be between"):
        await rest.set_monitor_volume(bus_id=20, volume=-5)

    # Too high
    with pytest.raises(ValueError, match="Volume must be between"):
        await rest.set_monitor_volume(bus_id=20, volume=110)


async def test_monitor_get_volume(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/monitor/{bus_id}/volume."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/volume",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"volume": 35}),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        volume = await rest.get_monitor_volume(bus_id=20)

        assert volume == 35


async def test_monitor_set_source(aresponses: ResponsesMockServer) -> None:
    """Test PUT /api/v1/monitor/{bus_id}/source."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.set_monitor_source(bus_id=20, source="HDMI1")


async def test_monitor_get_source(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/monitor/{bus_id}/source."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20/source",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({"source": "HDMI2"}),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        source = await rest.get_monitor_source(bus_id=20)

        assert source == "HDMI2"


async def test_browser_get_status(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/browser/status."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/browser/status",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("browser_state.json"),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        status = await rest.get_browser_status()

        assert status.url == "https://example.com"


async def test_browser_get_url(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/browser/url."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        url = await rest.get_browser_url()

        assert url == "https://example.com"


async def test_browser_set_url(aresponses: ResponsesMockServer) -> None:
    """Test POST /api/v1/browser/url."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.set_browser_url("https://example.com")


async def test_browser_refresh(aresponses: ResponsesMockServer) -> None:
    """Test POST /api/v1/browser/refresh."""
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
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.refresh_browser()


async def test_authentication_error(aresponses: ResponsesMockServer) -> None:
    """Test 401 Unauthorized response."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/status",
        METH_GET,
        aresponses.Response(
            status=401,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("error_unauthorized.json"),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="invalid-token")
        rest._session = session

        with pytest.raises(NetlinkAuthenticationError):
            await rest.get_desk_status()


async def test_connection_error(aresponses: ResponsesMockServer) -> None:
    """Test connection error handling."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/status",
        METH_GET,
        aresponses.Response(
            status=500,
            text="Internal Server Error",
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session

        with pytest.raises(NetlinkConnectionError):
            await rest.get_desk_status()


async def test_method_not_allowed_error(aresponses: ResponsesMockServer) -> None:
    """Test handling of HTTP 405 responses."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/height",
        METH_POST,
        aresponses.Response(
            status=405,
            headers={"Content-Type": "application/json"},
            text="Method Not Allowed",
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session

        with pytest.raises(
            NetlinkConnectionError, match="HTTP method POST not allowed"
        ):
            await rest._request("desk/height", method=METH_POST)


async def test_request_creates_session(aresponses: ResponsesMockServer) -> None:
    """Test _request creates its own session when needed."""
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

    rest = NetlinkREST(host="192.168.1.100", token="test-token")

    status = await rest.get_desk_status()

    assert status.height == 95.0
    assert rest._session is not None
    assert rest._close_session is True
    await rest.close()


async def test_timeout_error() -> None:
    """Test request timeout handling."""
    async with ClientSession() as session:
        rest = NetlinkREST(
            host="192.168.1.100", token="test-token", request_timeout=0.001
        )
        rest._session = session

        # Use a very long delay endpoint simulation
        with pytest.raises(NetlinkTimeoutError):
            await rest.get_desk_status()


async def test_bearer_token_header(aresponses: ResponsesMockServer) -> None:
    """Test that Bearer token is sent in Authorization header."""

    def check_auth_header(request: object) -> object:
        assert request.headers.get("Authorization") == "Bearer test-token-123"  # type: ignore[union-attr]
        return aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("desk_status_minimal.json"),
        )

    aresponses.add(
        "192.168.1.100",
        "/api/v1/desk/status",
        METH_GET,
        check_auth_header,
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token-123")
        rest._session = session
        await rest.get_desk_status()


async def test_request_client_error() -> None:
    """Test client error handling when session.request fails."""
    rest = NetlinkREST(host="192.168.1.100", token="test-token")

    mock_session = AsyncMock(spec=ClientSession)
    mock_session.request = AsyncMock(side_effect=ClientError("boom"))
    rest._session = mock_session

    with pytest.raises(NetlinkConnectionError, match="boom"):
        await rest.get_desk_status()


async def test_get_browser_status(aresponses: ResponsesMockServer) -> None:
    """Test GET /api/v1/browser/status."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/browser/status",
        METH_GET,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("browser_state.json"),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        status = await rest.get_browser_status()

        assert status.url == "https://example.com"


async def test_patch_monitor(aresponses: ResponsesMockServer) -> None:
    """Test PATCH /api/v1/monitor/{bus_id}."""
    aresponses.add(
        "192.168.1.100",
        "/api/v1/monitor/20",
        METH_PATCH,
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("success_response.json"),
        ),
    )

    async with ClientSession() as session:
        rest = NetlinkREST(host="192.168.1.100", token="test-token")
        rest._session = session
        await rest.patch_monitor(bus_id=20, brightness=75, power="on")


async def test_close_only_when_owned() -> None:
    """Test close only closes internally created session."""
    rest = NetlinkREST(host="192.168.1.100", token="test-token")
    rest._session = AsyncMock(spec=ClientSession)
    rest._session.close = AsyncMock()

    rest._close_session = True
    await rest.close()
    rest._session.close.assert_awaited_once()

    rest._session.close.reset_mock()
    rest._close_session = False
    await rest.close()
    rest._session.close.assert_not_called()


async def test_rest_context_manager_closes_session(
    aresponses: ResponsesMockServer,
) -> None:
    """Test async context manager closes internally created session."""
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

    async with NetlinkREST(host="192.168.1.100", token="test-token") as rest:
        status = await rest.get_desk_status()
        assert status.height == 95.0
        assert rest._session is not None

    assert rest._session is not None
    assert rest._session.closed is True
