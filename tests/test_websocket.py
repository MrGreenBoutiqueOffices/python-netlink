"""Tests for pynetlink WebSocket client."""

# pylint: disable=protected-access
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import socketio
from socketio import exceptions as socketio_exceptions

from pynetlink.exceptions import (
    NetlinkAuthenticationError,
    NetlinkAuthorizationError,
    NetlinkCommandError,
    NetlinkConnectionError,
    NetlinkMaintenanceGrantExpiredError,
    NetlinkMaintenanceRequiredError,
    NetlinkTimeoutError,
    NetlinkUnauthorizedError,
)
from pynetlink.websocket import NetlinkWebSocket


async def test_websocket_connect_success() -> None:
    """Test successful WebSocket connection."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        await ws.connect()

        assert ws.connected is True
        mock_sio.connect.assert_called_once_with(
            "http://192.168.1.100",
            auth={"token": "test-token"},
            transports=["websocket"],
        )


async def test_websocket_connect_auth_error() -> None:
    """Test WebSocket connection with invalid token."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="invalid-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock(
            side_effect=socketio_exceptions.ConnectionError("Authentication failed")
        )
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        with pytest.raises(NetlinkAuthenticationError, match="Authentication failed"):
            await ws.connect()

        assert ws.connected is False


async def test_websocket_connect_timeout() -> None:
    """Test WebSocket connection timeout."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        # Simulate timeout by raising TimeoutError
        mock_sio.connect = AsyncMock(side_effect=TimeoutError("Connection timeout"))

        with pytest.raises(NetlinkTimeoutError, match="timed out"):
            await ws.connect()


async def test_websocket_disconnect() -> None:
    """Test WebSocket disconnection."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.shutdown = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        # Connect first
        await ws.connect()
        assert ws.connected is True

        # Then disconnect
        await ws.disconnect()
        assert ws.connected is False
        mock_sio.shutdown.assert_awaited_once()


async def test_websocket_event_subscription() -> None:
    """Test event subscription with decorator."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio

        # Track registered events
        registered_events = {}

        def mock_on(event: str) -> Any:
            def decorator(callback: Any) -> Any:
                registered_events[event] = callback
                return callback

            return decorator

        mock_sio.on = mock_on

        # Subscribe to event using decorator
        callback_called = False

        @ws.on("desk.state")
        async def on_desk_state(_data: dict) -> None:
            nonlocal callback_called
            callback_called = True

        # Verify callback was registered
        assert "desk.state" in ws._callbacks
        assert len(ws._callbacks["desk.state"]) == 1

        # Call the callback
        await ws._callbacks["desk.state"][0]({"height": 75.0})
        assert callback_called is True


async def test_websocket_multiple_callbacks_same_event() -> None:
    """Test multiple callbacks for the same event."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Subscribe multiple callbacks to same event
        results = []

        @ws.on("desk.state")
        async def callback1(data: dict) -> None:
            results.append(f"callback1: {data['height']}")

        @ws.on("desk.state")
        async def callback2(data: dict) -> None:
            results.append(f"callback2: {data['height']}")

        # Verify both callbacks registered
        assert len(ws._callbacks["desk.state"]) == 2

        # Emit to all callbacks
        await ws.emit_to_callbacks("desk.state", {"height": 100.0})

        # Both callbacks should have been called
        assert len(results) == 2
        assert "callback1: 100.0" in results
        assert "callback2: 100.0" in results


async def test_websocket_emit_to_callbacks_sync() -> None:
    """Test emit_to_callbacks with synchronous callback."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    result = []

    # Register synchronous callback
    def sync_callback(data: dict) -> None:
        result.append(data["value"])

    ws._callbacks["test.event"] = [sync_callback]

    # Emit event
    await ws.emit_to_callbacks("test.event", {"value": "test"})

    # Verify sync callback was called
    assert result == ["test"]


async def test_websocket_emit_to_callbacks_async() -> None:
    """Test emit_to_callbacks with asynchronous callback."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    result = []

    # Register async callback
    async def async_callback(data: dict) -> None:
        result.append(data["value"])

    ws._callbacks["test.event"] = [async_callback]

    # Emit event
    await ws.emit_to_callbacks("test.event", {"value": "async_test"})

    # Verify async callback was called
    assert result == ["async_test"]


async def test_websocket_emit_to_unknown_event() -> None:
    """Test emit_to_callbacks with event that has no callbacks."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    # This should not raise an error
    await ws.emit_to_callbacks("unknown.event", {"data": "test"})


async def test_websocket_connected_property() -> None:
    """Test connected property tracking."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    # Initially not connected
    assert ws.connected is False

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.disconnect = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        # After connect
        await ws.connect()
        assert ws.connected is True

        # After disconnect
        await ws.disconnect()
        assert ws.connected is False


async def test_websocket_connect_without_previous_disconnect() -> None:
    """Test connecting when already connected."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.disconnect = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        # First connect
        await ws.connect()
        assert ws.connected is True

        # A duplicate connect is ignored to prevent overlapping attempts.
        await ws.connect()
        assert ws.connected is True

        mock_sio.connect.assert_awaited_once()


async def test_websocket_disconnect_when_not_connected() -> None:
    """Test disconnecting when not connected."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    # This should not raise an error
    await ws.disconnect()
    assert ws.connected is False


async def test_websocket_event_registration_before_connect() -> None:
    """Test registering event handlers before connecting."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    called = False

    @ws.on("desk.state")
    async def handler(_data: dict) -> None:
        nonlocal called
        called = True

    # Callback should be registered even without connection
    assert "desk.state" in ws._callbacks
    assert len(ws._callbacks["desk.state"]) == 1

    # And should be callable
    await ws.emit_to_callbacks("desk.state", {"height": 75.0})
    assert called is True


async def test_websocket_connect_registers_existing_callbacks() -> None:
    """Test that callbacks added before connect are registered with Socket.IO."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    received: list[float] = []

    @ws.on("desk.state")
    def handler(data: dict) -> None:
        received.append(data["height"])

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()

        registered_wrappers = {}

        def mock_on(event: str) -> Any:
            def decorator(wrapper: Any) -> Any:
                registered_wrappers[event] = wrapper
                return wrapper

            return decorator

        mock_sio.on = mock_on

        await ws.connect()

        assert "desk.state" in registered_wrappers
        await registered_wrappers["desk.state"]({"data": {"height": 91.0}})

    assert received == [91.0]


async def test_websocket_connect_dispatches_multiple_callbacks_per_event() -> None:
    """One Socket.IO handler dispatches every callback for the same event."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")
    received: list[str] = []

    @ws.on("authorization.state")
    async def update_cache(_data: dict) -> None:
        received.append("cache")

    @ws.on("authorization.state")
    async def notify_user(_data: dict) -> None:
        received.append("user")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        registered_handlers: dict[str, Any] = {}

        def mock_on(event: str) -> Any:
            def decorator(handler: Any) -> Any:
                registered_handlers[event] = handler
                return handler

            return decorator

        mock_sio.on = mock_on

        await ws.connect()
        await registered_handlers["authorization.state"]({"policy_version": 1})

    assert received == ["cache", "user"]


async def test_websocket_wrapper_accepts_no_payload() -> None:
    """Test wrapper handles events without payload."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    seen: list[dict] = []

    @ws.on("ready")
    def on_ready(data: dict) -> None:
        seen.append(data)

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()

        registered_wrappers = {}

        def mock_on(event: str) -> Any:
            def decorator(wrapper: Any) -> Any:
                registered_wrappers[event] = wrapper
                return wrapper

            return decorator

        mock_sio.on = mock_on

        await ws.connect()

        assert "ready" in registered_wrappers
        await registered_wrappers["ready"]()

    assert seen == [{}]


async def test_websocket_wrapper_ignores_extra_args() -> None:
    """Test wrapper uses first arg when multiple are provided."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    seen: list[dict] = []

    @ws.on("ready")
    def on_ready(data: dict) -> None:
        seen.append(data)

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()

        registered_wrappers = {}

        def mock_on(event: str) -> Any:
            def decorator(wrapper: Any) -> Any:
                registered_wrappers[event] = wrapper
                return wrapper

            return decorator

        mock_sio.on = mock_on

        await ws.connect()

        assert "ready" in registered_wrappers
        await registered_wrappers["ready"]({"data": {"height": 120}}, {"ignored": True})

    assert seen == [{"height": 120}]


async def test_websocket_connect_registers_async_callback_without_dict() -> None:
    """Test wrapper handles non-dict payload for async callback."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    seen: list[str] = []

    @ws.on("ping")
    async def on_ping(data: str) -> None:
        seen.append(data)

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()

        registered_wrappers = {}

        def mock_on(event: str) -> Any:
            def decorator(wrapper: Any) -> Any:
                registered_wrappers[event] = wrapper
                return wrapper

            return decorator

        mock_sio.on = mock_on

        await ws.connect()

        assert "ping" in registered_wrappers
        await registered_wrappers["ping"]("pong")

    assert seen == ["pong"]


async def test_websocket_connect_with_auth_error() -> None:
    """Test WebSocket connection with authentication error."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="invalid")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock(
            side_effect=socketio_exceptions.ConnectionError("unauthorized access")
        )
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        with pytest.raises(NetlinkAuthenticationError, match="Authentication failed"):
            await ws.connect()


async def test_websocket_connect_with_generic_error() -> None:
    """Test WebSocket connection with unexpected error."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        with pytest.raises(NetlinkConnectionError, match="Unexpected error"):
            await ws.connect()


async def test_websocket_existing_client_surfaces_transport_error() -> None:
    """A reused Socket.IO client translates a generic connection failure."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")
    mock_sio = AsyncMock()
    mock_sio.connect.side_effect = socketio_exceptions.ConnectionError(
        "Network unavailable"
    )
    ws._sio = mock_sio

    with pytest.raises(NetlinkConnectionError, match="Failed to connect"):
        await ws.connect()


async def test_websocket_event_registration_with_connection() -> None:
    """Test registering event after connection creates wrapper."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()

        # Track what gets registered with Socket.IO
        registered_wrappers = {}

        def mock_on(event: str) -> Any:
            def decorator(wrapper: Any) -> Any:
                registered_wrappers[event] = wrapper
                return wrapper

            return decorator

        mock_sio.on = mock_on

        # Connect first
        await ws.connect()

        # Now register callback - should create wrapper
        result = []

        @ws.on("desk.state")
        async def handler(data: dict) -> None:
            result.append(data["height"])

        # Wrapper should be registered with Socket.IO
        assert "desk.state" in registered_wrappers

        # Call the wrapper with nested data
        await registered_wrappers["desk.state"]({"data": {"height": 100.0}})

        # Handler should have received unwrapped data
        assert result == [100.0]


async def test_websocket_sync_callback_wrapper_with_connection() -> None:
    """Test sync callbacks registered after connect unwrap data."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = MagicMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()

        registered_wrappers = {}

        def mock_on(event: str) -> Any:
            def decorator(wrapper: Any) -> Any:
                registered_wrappers[event] = wrapper
                return wrapper

            return decorator

        mock_sio.on = mock_on

        await ws.connect()

        values: list[float] = []

        @ws.on("desk.state")
        def handle(data: dict) -> None:
            values.append(data["height"])

        assert "desk.state" in registered_wrappers
        await registered_wrappers["desk.state"]({"data": {"height": 77.0}})

        assert values == [77.0]


async def test_websocket_configures_socketio_reconnection() -> None:
    """Socket.IO is the sole owner of explicitly bounded reconnection."""
    ws = NetlinkWebSocket(
        host="192.168.1.100",
        token="test-token",
        reconnect_delay=2.0,
        max_reconnect_delay=30.0,
    )

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)

        await ws.connect()

    mock_client_class.assert_called_once_with(
        reconnection=True,
        reconnection_delay=2.0,
        reconnection_delay_max=30.0,
        randomization_factor=0,
    )


async def test_websocket_disconnect_uses_socketio_shutdown() -> None:
    """Intentional shutdown also aborts Socket.IO's reconnect loop."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")
    mock_sio = AsyncMock()
    ws._sio = mock_sio

    await ws.disconnect()

    mock_sio.shutdown.assert_awaited_once()
    assert ws._sio is None
    assert ws.connected is False


async def test_websocket_on_connect_event() -> None:
    """Test _on_connect event handler."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    connect_called = False

    @ws.on("connect")
    async def on_connect(_data: dict) -> None:
        nonlocal connect_called
        connect_called = True

    # Simulate connect event
    ws._on_connect()

    # Yield control to event loop to let scheduled task run
    await asyncio.sleep(0)

    assert ws.connected is True
    assert connect_called is True


async def test_websocket_on_disconnect_event() -> None:
    """Test _on_disconnect event handler."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")
    ws._connected = True  # Set as connected first

    disconnect_called = False

    @ws.on("disconnect")
    async def on_disconnect(_data: dict) -> None:
        nonlocal disconnect_called
        disconnect_called = True

    # Simulate disconnect event
    ws._on_disconnect()

    # Yield control to event loop to let scheduled task run
    await asyncio.sleep(0)

    assert ws.connected is False
    assert disconnect_called is True


async def test_websocket_connect_error_callback_is_sanitized() -> None:
    """Connection failures are typed without echoing server details or tokens."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="secret-token")
    errors: list[dict[str, str]] = []

    @ws.on("connect_error")
    async def on_connect_error(data: dict[str, str]) -> None:
        errors.append(data)

    ws._on_connect_error({"message": "Unauthorized: secret-token"})
    await asyncio.sleep(0)

    assert errors == [
        {
            "type": "authentication",
            "message": "Authentication failed for 192.168.1.100",
        }
    ]


async def test_websocket_connect_error_without_payload_is_transport_error() -> None:
    """A payload-less Socket.IO failure remains a useful transport event."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="secret-token")
    errors: list[dict[str, str]] = []

    @ws.on("connect_error")
    async def on_connect_error(data: dict[str, str]) -> None:
        errors.append(data)

    ws._on_connect_error()
    await asyncio.sleep(0)

    assert errors == [
        {
            "type": "transport",
            "message": "Connection to 192.168.1.100 failed",
        }
    ]


async def test_websocket_send_command_success() -> None:
    """Test sending command via WebSocket with successful acknowledgement."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.emit = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Connect first
        await ws.connect()
        assert ws.connected is True

        # Start send_command task
        command_task = asyncio.create_task(
            ws.send_command("command.desk.height", {"height": 120.0})
        )

        # Wait for command to be emitted
        await asyncio.sleep(0.01)

        # Verify command was emitted
        assert mock_sio.emit.call_count == 1
        emit_args = mock_sio.emit.call_args[0]
        assert emit_args[0] == "command"
        command_payload = emit_args[1]
        assert command_payload["type"] == "command.desk.height"
        assert command_payload["data"] == {"height": 120.0}
        assert "id" in command_payload

        # Simulate server acknowledgement
        command_id = command_payload["id"]
        ws._on_command_ack({"data": {"id": command_id, "status": "ok"}})

        # Wait for command to complete
        result = await command_task
        assert result["status"] == "ok"


async def test_websocket_send_command_error() -> None:
    """Test sending command that returns error from server."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.emit = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Connect first
        await ws.connect()

        # Start send_command task
        command_task = asyncio.create_task(
            ws.send_command("command.desk.height", {"height": 200.0})  # Invalid height
        )

        # Wait for command to be emitted
        await asyncio.sleep(0.01)

        # Get command ID
        emit_args = mock_sio.emit.call_args[0]
        command_payload = emit_args[1]
        command_id = command_payload["id"]

        # Simulate server error response
        ws._on_command_ack(
            {
                "data": {
                    "id": command_id,
                    "status": "error",
                    "error": "Height out of range",
                    "command": "command.desk.height",
                }
            }
        )

        # Command should raise NetlinkCommandError
        with pytest.raises(NetlinkCommandError, match="Height out of range"):
            await command_task


@pytest.mark.parametrize(
    ("error_code", "exception_type"),
    [
        ("unauthorized", NetlinkUnauthorizedError),
        ("maintenance_required", NetlinkMaintenanceRequiredError),
        ("maintenance_grant_expired", NetlinkMaintenanceGrantExpiredError),
    ],
)
async def test_websocket_maps_authorization_command_errors(
    error_code: str,
    exception_type: type[NetlinkAuthorizationError],
) -> None:
    """Stable acknowledgement denials map to typed public exceptions."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")
    command_id = "command-id"
    future: asyncio.Future[dict[str, Any]] = asyncio.Future()
    ws._pending_commands[command_id] = future

    ws._on_command_ack(
        {
            "data": {
                "id": command_id,
                "status": "error",
                "error": error_code,
                "command": "command.system.reboot",
            }
        }
    )

    with pytest.raises(exception_type, match=error_code) as error:
        await future

    assert isinstance(error.value, NetlinkCommandError)
    assert error.value.command == "command.system.reboot"
    assert error.value.error_details is not None


async def test_websocket_send_command_timeout() -> None:
    """Test command timeout when no acknowledgement received."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.emit = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Connect first
        await ws.connect()

        # Send command with very short timeout, no acknowledgement will arrive
        with pytest.raises(NetlinkTimeoutError, match="timed out"):
            await ws.send_command(
                "command.desk.height",
                {"height": 120.0},
                command_timeout=0.05,  # Very short timeout
            )


async def test_websocket_send_command_not_connected() -> None:
    """Test sending command when not connected."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    # Try to send command without connecting
    with pytest.raises(NetlinkConnectionError, match="Not connected"):
        await ws.send_command("command.desk.height", {"height": 120.0})


async def test_websocket_send_command_no_data() -> None:
    """Test sending command without data payload."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.emit = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Connect first
        await ws.connect()

        # Start send_command task without data
        command_task = asyncio.create_task(ws.send_command("command.desk.stop"))

        # Wait for command to be emitted
        await asyncio.sleep(0.01)

        # Verify command was emitted without data field
        emit_args = mock_sio.emit.call_args[0]
        command_payload = emit_args[1]
        assert command_payload["type"] == "command.desk.stop"
        assert "data" not in command_payload or command_payload.get("data") is None

        # Simulate acknowledgement
        command_id = command_payload["id"]
        ws._on_command_ack({"data": {"id": command_id, "status": "ok"}})

        # Wait for command to complete
        result = await command_task
        assert result["status"] == "ok"


async def test_websocket_disconnect_cancels_pending_commands() -> None:
    """Test that disconnect cancels all pending commands."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.emit = AsyncMock()
        mock_sio.disconnect = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Connect first
        await ws.connect()

        # Start multiple commands
        command1_task = asyncio.create_task(
            ws.send_command("command.desk.height", {"height": 120.0})
        )
        command2_task = asyncio.create_task(ws.send_command("command.desk.stop"))

        # Wait for commands to be emitted
        await asyncio.sleep(0.01)

        # Trigger disconnect (simulating server disconnect)
        ws._on_disconnect()

        # Both commands should fail with connection error
        with pytest.raises(NetlinkConnectionError, match="Disconnected while waiting"):
            await command1_task

        with pytest.raises(NetlinkConnectionError, match="Disconnected while waiting"):
            await command2_task

        # Pending commands should be cleared
        assert len(ws._pending_commands) == 0


async def test_websocket_disconnect_ignores_completed_commands() -> None:
    """Test disconnect does not error when pending command already finished."""
    ws = NetlinkWebSocket(
        host="192.168.1.100",
        token="test-token",
        auto_reconnect=False,
    )

    finished_future: asyncio.Future[dict[str, Any]] = asyncio.Future()
    finished_future.set_result({"status": "ok"})
    ws._pending_commands["done"] = finished_future

    # Should not raise even though future is already done
    ws._on_disconnect()
    assert not ws._pending_commands


async def test_websocket_command_ack_unknown_id() -> None:
    """Test handling acknowledgement for unknown command ID."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    # Simulate ack for unknown command (should not crash)
    ws._on_command_ack({"data": {"id": "unknown-uuid", "status": "ok"}})

    # Should complete without error
    assert True


async def test_websocket_command_ack_without_id() -> None:
    """Test handling malformed acknowledgement without ID."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    # Simulate malformed ack (should not crash)
    ws._on_command_ack({"data": {"status": "ok"}})

    # Should complete without error
    assert True


async def test_websocket_send_command_bad_namespace_error() -> None:
    """Test send_command raises NetlinkConnectionError on BadNamespaceError."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.on = MagicMock(return_value=lambda f: f)
        mock_sio.emit = AsyncMock(
            side_effect=socketio_exceptions.BadNamespaceError("disconnected")
        )

        await ws.connect()
        assert ws.connected is True

        with pytest.raises(NetlinkConnectionError, match="disconnected while sending"):
            await ws.send_command("command.desk.height", {"height": 120.0})
