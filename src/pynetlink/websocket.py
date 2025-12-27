"""WebSocket/Socket.IO handler for Netlink devices."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import socketio  # pyright: ignore[reportMissingImports]
from socketio import exceptions as socketio_exceptions

from .const import (
    DEFAULT_COMMAND_TIMEOUT,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_RECONNECT_DELAY,
    MAX_RECONNECT_DELAY,
)
from .exceptions import (
    NetlinkAuthenticationError,
    NetlinkCommandError,
    NetlinkConnectionError,
    NetlinkTimeoutError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)


@dataclass
class NetlinkWebSocket:
    """WebSocket client for real-time Netlink events.

    Handles Socket.IO connection, authentication, and event subscription.

    Args:
    ----
        host: Hostname or IP address
        token: Bearer authentication token
        auto_reconnect: Enable automatic reconnection on disconnect
        reconnect_delay: Initial delay between reconnection attempts (seconds)
        max_reconnect_delay: Maximum delay between reconnection attempts (seconds)

    """

    host: str
    token: str
    auto_reconnect: bool = True
    reconnect_delay: float = DEFAULT_RECONNECT_DELAY
    max_reconnect_delay: float = MAX_RECONNECT_DELAY

    # Internal state
    _sio: socketio.AsyncClient | None = field(default=None, init=False, repr=False)
    _callbacks: dict[str, list[Callable]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _connected: bool = field(default=False, init=False, repr=False)
    _reconnect_task: asyncio.Task | None = field(default=None, init=False, repr=False)
    _should_reconnect: bool = field(default=True, init=False, repr=False)
    _current_delay: float = field(init=False, repr=False)

    # Command acknowledgement tracking
    _pending_commands: dict[str, asyncio.Future[dict[str, Any]]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Initialize internal state after dataclass initialization."""
        self._current_delay = self.reconnect_delay

    async def connect(self) -> None:
        """Connect to Netlink WebSocket.

        Raises
        ------
            NetlinkAuthenticationError: Invalid token
            NetlinkConnectionError: Connection failed
            NetlinkTimeoutError: Connection timeout

        """
        if self._sio is None:
            self._sio = socketio.AsyncClient()

            # Register Socket.IO built-in event handlers
            self._sio.on("connect")(self._on_connect)
            self._sio.on("disconnect")(self._on_disconnect)

            # Register command acknowledgement handler
            self._sio.on("command_ack")(self._on_command_ack)

            # Register any callbacks that were added before connect()
            for event, callbacks in self._callbacks.items():
                for callback in callbacks:
                    self._sio.on(event)(self._wrap_callback(callback))

        try:
            async with asyncio.timeout(DEFAULT_CONNECT_TIMEOUT):
                await self._sio.connect(
                    f"http://{self.host}",
                    auth={"token": self.token},
                    transports=["websocket"],
                )
                self._connected = True
                self._current_delay = (
                    self.reconnect_delay
                )  # Reset delay on successful connect
        except TimeoutError as err:
            msg = f"Connection to {self.host} timed out"
            raise NetlinkTimeoutError(msg) from err
        except socketio_exceptions.ConnectionError as err:
            # Check if it's an auth error (Socket.IO returns False from connect handler)
            if "unauthorized" in str(err).lower():
                msg = f"Authentication failed for {self.host}"
                raise NetlinkAuthenticationError(msg) from err
            msg = f"Failed to connect to {self.host}: {err}"
            raise NetlinkConnectionError(msg) from err
        except Exception as err:
            msg = f"Unexpected error connecting to {self.host}: {err}"
            raise NetlinkConnectionError(msg) from err

    async def disconnect(self) -> None:
        """Disconnect from WebSocket and stop auto-reconnection."""
        self._should_reconnect = False

        # Cancel any pending reconnection task
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reconnect_task

        if self._sio and self._connected:
            await self._sio.disconnect()
            self._sio = None
            self._connected = False

    def on(self, event: str) -> Callable[[Callable], Callable]:
        """Subscribe to WebSocket event.

        Args:
        ----
            event: Event name (e.g., "desk.state", "display.state")

        Returns:
        -------
            Decorator function

        Examples:
        --------
            >>> ws = NetlinkWebSocket("host", "token")
            >>> @ws.on("desk.state")
            >>> async def handler(data):
            >>>     print(data)

        """

        def decorator(callback: Callable) -> Callable:
            # Store original callback in our registry
            if event not in self._callbacks:
                self._callbacks[event] = []
            self._callbacks[event].append(callback)

            # Register wrapper with Socket.IO
            if self._sio:
                self._sio.on(event)(self._wrap_callback(callback))

            return callback

        return decorator

    def _wrap_callback(self, callback: Callable) -> Callable:
        """Wrap a callback to normalize Socket.IO event payloads."""

        async def wrapper(*args: Any) -> None:
            if len(args) > 1:
                _LOGGER.debug(
                    "Socket.IO event passed %d args; using first payload.",
                    len(args),
                )
            raw_data = args[0] if args else {}
            data = (
                raw_data.get("data", raw_data)
                if isinstance(raw_data, dict)
                else raw_data
            )
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)

        return wrapper

    async def emit_to_callbacks(self, event: str, data: Any) -> None:
        """Emit event to registered callbacks.

        Args:
        ----
            event: Event name
            data: Event data

        """
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)

    async def send_command(
        self,
        command_type: str,
        data: dict[str, Any] | None = None,
        command_timeout: float = DEFAULT_COMMAND_TIMEOUT,
    ) -> dict[str, Any]:
        """Send command via WebSocket and wait for acknowledgement.

        Args:
        ----
            command_type: Command type (e.g., "command.desk.height")
            data: Command data payload
            command_timeout: Timeout in seconds for acknowledgement

        Returns:
        -------
            Command acknowledgement data

        Raises:
        ------
            NetlinkConnectionError: Not connected to WebSocket
            NetlinkTimeoutError: No acknowledgement received within timeout
            NetlinkCommandError: Command execution failed (status=error)

        Examples:
        --------
            >>> await ws.send_command("command.desk.height", {"height": 120.0})
            {'id': '...', 'status': 'ok'}

        """
        if not self._connected or not self._sio:
            msg = "Not connected to WebSocket"
            raise NetlinkConnectionError(msg)

        # Generate unique command ID
        command_id = str(uuid.uuid4())

        # Create future for acknowledgement
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        self._pending_commands[command_id] = future

        # Build command payload
        payload = {
            "type": command_type,
            "id": command_id,
        }
        if data:
            payload["data"] = data

        try:
            # Send command via Socket.IO
            await self._sio.emit("command", payload)

            # Wait for acknowledgement with timeout
            async with asyncio.timeout(command_timeout):
                return await future

        except TimeoutError as err:
            # Clean up pending command
            self._pending_commands.pop(command_id, None)
            msg = (
                f"Command {command_type} ({command_id}) timed out after "
                f"{command_timeout}s"
            )
            raise NetlinkTimeoutError(msg) from err

        except Exception:
            # Clean up pending command
            self._pending_commands.pop(command_id, None)
            raise

    @property
    def connected(self) -> bool:
        """Whether WebSocket is connected."""
        return self._connected

    def _on_connect(self) -> None:
        """Handle Socket.IO connect event."""
        _LOGGER.info("Connected to %s", self.host)
        self._connected = True
        self._current_delay = self.reconnect_delay  # Reset backoff delay

        # Emit connect event to user callbacks (fire-and-forget task)
        asyncio.create_task(self.emit_to_callbacks("connect", {}))  # noqa: RUF006

    def _on_disconnect(self) -> None:
        """Handle Socket.IO disconnect event."""
        _LOGGER.warning("Disconnected from %s", self.host)
        self._connected = False

        # Emit disconnect event to user callbacks (fire-and-forget task)
        asyncio.create_task(self.emit_to_callbacks("disconnect", {}))  # noqa: RUF006

        # Cancel all pending commands
        for command_id, future in self._pending_commands.items():
            if not future.done():
                future.set_exception(
                    NetlinkConnectionError(
                        f"Disconnected while waiting for command {command_id}"
                    ),
                )
        self._pending_commands.clear()

        # Start auto-reconnection if enabled and not intentionally disconnected
        if self.auto_reconnect and self._should_reconnect:
            _LOGGER.info("Auto-reconnection enabled, scheduling reconnect")
            self._reconnect_task = asyncio.create_task(self._auto_reconnect())

    def _on_command_ack(self, ack_data: dict[str, Any]) -> None:
        """Handle command acknowledgement from server.

        Args:
        ----
            ack_data: Acknowledgement data with structure:
                {
                    "type": "command_ack",
                    "data": {
                        "id": "command-uuid",
                        "status": "ok" or "error",
                        "error": "optional error message"
                    },
                    "ts": "2025-12-16T12:00:00Z"
                }

        """
        # Extract nested data if present
        data = (
            ack_data.get("data", ack_data) if isinstance(ack_data, dict) else ack_data
        )

        command_id = data.get("id")
        status = data.get("status")

        if not command_id:
            _LOGGER.warning("Received command_ack without id: %s", ack_data)
            return

        future = self._pending_commands.pop(command_id, None)
        if not future or future.done():
            _LOGGER.debug(
                "Received ack for unknown or completed command: %s", command_id
            )
            return

        if status == "error":
            # Command failed
            error_msg = data.get("error", "Command execution failed")
            command_type = data.get("command", "unknown")
            future.set_exception(
                NetlinkCommandError(
                    error_msg,
                    command=command_type,
                    error_details=data,
                ),
            )
        else:
            # Command succeeded
            future.set_result(data)

    async def _auto_reconnect(self) -> None:
        """Automatically reconnect with exponential backoff."""
        while self._should_reconnect:
            try:
                _LOGGER.info(
                    "Attempting to reconnect to %s in %.1f seconds...",
                    self.host,
                    self._current_delay,
                )
                await asyncio.sleep(self._current_delay)

                # Try to reconnect
                await self.connect()
            except NetlinkAuthenticationError:
                # Don't retry on auth errors
                _LOGGER.exception("Reconnection failed: Authentication error")
                self._should_reconnect = False
                return

            except (NetlinkConnectionError, NetlinkTimeoutError) as err:
                # Increase delay with exponential backoff
                self._current_delay = min(
                    self._current_delay * 2,
                    self.max_reconnect_delay,
                )
                _LOGGER.warning(
                    "Reconnection attempt failed: %s. Next attempt in %.1f seconds",
                    err,
                    self._current_delay,
                )

            except asyncio.CancelledError:
                _LOGGER.info("Reconnection task cancelled")
                return

            else:
                # Connection successful
                _LOGGER.info("Successfully reconnected to %s", self.host)
                return
