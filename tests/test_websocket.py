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
    NetlinkCommandError,
    NetlinkConnectionError,
    NetlinkTimeoutError,
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

        with pytest.raises(NetlinkConnectionError, match="Failed to connect"):
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
        mock_sio.disconnect = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)  # Fix: non-async decorator

        # Connect first
        await ws.connect()
        assert ws.connected is True

        # Then disconnect
        await ws.disconnect()
        assert ws.connected is False
        mock_sio.disconnect.assert_called_once()


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

        # Second connect (should reuse same client)
        await ws.connect()
        assert ws.connected is True

        # Connect should only be called twice (once per connect call)
        assert mock_sio.connect.call_count == 2


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


async def test_websocket_wrapper_accepts_no_payload() -> None:
    """Test wrapper handles events without payload."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    seen: list[dict] = []

    @ws.on("connect")
    def on_connect(data: dict) -> None:
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

        assert "connect" in registered_wrappers
        await registered_wrappers["connect"]()

    assert seen == [{}]


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


async def test_websocket_auto_reconnect_disabled() -> None:
    """Test WebSocket with auto-reconnect disabled."""
    ws = NetlinkWebSocket(
        host="192.168.1.100",
        token="test-token",
        auto_reconnect=False,
    )

    # Simulate disconnect event
    ws._on_disconnect()

    # No reconnection task should be created
    assert ws._reconnect_task is None


async def test_websocket_disconnect_cancels_reconnect() -> None:
    """Test that disconnect cancels pending reconnection."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.connect = AsyncMock()
        mock_sio.disconnect = AsyncMock()
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Connect
        await ws.connect()

        # Simulate disconnect to trigger auto-reconnect
        ws._on_disconnect()

        # Verify reconnect task was created
        assert ws._reconnect_task is not None
        assert not ws._reconnect_task.done()

        # Now disconnect - should cancel the task
        await ws.disconnect()

        # Verify task was cancelled
        assert ws._reconnect_task.done()


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


async def test_websocket_auto_reconnect_exponential_backoff() -> None:
    """Test auto-reconnect with exponential backoff."""
    ws = NetlinkWebSocket(
        host="192.168.1.100",
        token="test-token",
        reconnect_delay=0.01,  # Short delay for fast test
        max_reconnect_delay=0.08,  # Max is 8x initial delay
    )

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # First 3 attempts fail, 4th succeeds
        mock_sio.connect = AsyncMock(
            side_effect=[
                socketio_exceptions.ConnectionError("Failed 1"),
                socketio_exceptions.ConnectionError("Failed 2"),
                socketio_exceptions.ConnectionError("Failed 3"),
                None,  # Success
            ]
        )

        # Start auto-reconnect
        # Will try: 0.01s -> fail -> 0.02s -> fail -> 0.04s -> fail -> 0.08s -> success
        reconnect_task = asyncio.create_task(ws._auto_reconnect())

        # Wait for reconnection to complete (~0.15s total)
        await asyncio.wait_for(reconnect_task, timeout=1.0)

        # After successful reconnection, delay should be reset to initial value
        assert ws.connected is True
        assert ws._current_delay == 0.01


async def test_websocket_auto_reconnect_stops_on_auth_error() -> None:
    """Test auto-reconnect stops on authentication error."""
    ws = NetlinkWebSocket(
        host="192.168.1.100",
        token="invalid",
        reconnect_delay=0.01,  # Very short delay for faster test
    )

    with patch.object(socketio, "AsyncClient") as mock_client_class:
        mock_sio = AsyncMock()
        mock_client_class.return_value = mock_sio
        mock_sio.on = MagicMock(return_value=lambda f: f)

        # Simulate authentication error - use "unauthorized" keyword
        # connect() checks for "unauthorized" (case-insensitive)
        mock_sio.connect = AsyncMock(
            side_effect=socketio_exceptions.ConnectionError("Unauthorized access")
        )

        # Start auto-reconnect
        reconnect_task = asyncio.create_task(ws._auto_reconnect())

        # Wait for it to stop (should detect auth error and stop immediately)
        await asyncio.wait_for(reconnect_task, timeout=1.0)

        # Should have stopped reconnecting after detecting auth error
        assert ws._should_reconnect is False
        # Connect is called once - then auth error stops reconnection
        assert mock_sio.connect.call_count == 1


async def test_websocket_auto_reconnect_unexpected_error_then_success() -> None:
    """Test auto-reconnect handles connection errors and retries."""
    ws = NetlinkWebSocket(
        host="192.168.1.100",
        token="test-token",
        reconnect_delay=0.0,
        max_reconnect_delay=0.01,
    )

    # First attempt raises generic error, second succeeds
    ws_connect_mock = AsyncMock(side_effect=[NetlinkConnectionError("boom"), None])

    with (
        patch.object(ws, "connect", ws_connect_mock),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        reconnect_task = asyncio.create_task(ws._auto_reconnect())
        await asyncio.wait_for(reconnect_task, timeout=1.0)

    # After unexpected error we should have retried
    assert ws_connect_mock.call_count == 2


async def test_websocket_auto_reconnect_skips_when_disabled() -> None:
    """Test auto-reconnect exits immediately when disabled."""
    ws = NetlinkWebSocket(host="192.168.1.100", token="test-token")
    ws._should_reconnect = False

    await ws._auto_reconnect()


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
