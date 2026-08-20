"""Integration tests against a real local Socket.IO server."""

# pylint: disable=protected-access
from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest
import socketio
from aiohttp import web
from socketio import exceptions as socketio_exceptions

from pynetlink.exceptions import (
    NetlinkAuthenticationError,
    NetlinkConnectionError,
)
from pynetlink.websocket import NetlinkWebSocket

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class LocalSocketIOServer:
    """Small restartable Socket.IO server used to exercise transport behavior."""

    runner: web.AppRunner
    port: int
    connect_attempts: int = 0

    @classmethod
    async def start(
        cls,
        *,
        port: int = 0,
        accepted_token: str | None = None,
    ) -> LocalSocketIOServer:
        """Start a server that rejects any other bearer token."""
        accepted_token = accepted_token or "valid-token"
        server = socketio.AsyncServer(async_mode="aiohttp")
        app = web.Application()
        server.attach(app)
        runner = web.AppRunner(app, shutdown_timeout=0.01)
        instance = cls(runner=runner, port=port)

        @server.event
        async def connect(
            _sid: str,
            _environ: dict[str, Any],
            auth: dict[str, Any] | None,
        ) -> None:
            instance.connect_attempts += 1
            if not auth or auth.get("token") != accepted_token:
                message = "Authentication failed"
                raise socketio_exceptions.ConnectionRefusedError(message)

        await runner.setup()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("127.0.0.1", port))
        server_socket.settimeout(0)
        instance.port = server_socket.getsockname()[1]
        site = web.SockSite(runner, server_socket)
        await site.start()
        return instance

    async def stop(self) -> None:
        """Stop the server and close active WebSocket connections."""
        await self.runner.cleanup()


async def _wait_until(
    predicate: Callable[[], bool],
    *,
    wait_seconds: float = 3.0,
) -> None:
    """Wait for asynchronous transport state to satisfy a predicate."""
    async with asyncio.timeout(wait_seconds):
        while not predicate():  # noqa: ASYNC110
            await asyncio.sleep(0.01)


async def test_socketio_reconnect_failure_recovery_and_shutdown() -> None:
    """Socket.IO retries network loss, recovers, and stops on shutdown."""
    server = await LocalSocketIOServer.start()
    port = server.port
    replacement: LocalSocketIOServer | None = None
    ws = NetlinkWebSocket(
        host=f"127.0.0.1:{port}",
        token="valid-token",
        reconnect_delay=0.05,
        max_reconnect_delay=0.1,
    )
    connections = 0
    connection_errors: list[dict[str, str]] = []

    @ws.on("connect")
    async def on_connect(_data: dict[str, Any]) -> None:
        nonlocal connections
        connections += 1

    @ws.on("connect_error")
    async def on_connect_error(data: dict[str, str]) -> None:
        connection_errors.append(data)

    try:
        await ws.connect()
        await _wait_until(lambda: connections == 1)

        command_task = asyncio.create_task(
            ws.send_command("command.no_ack", command_timeout=2.0)
        )
        await _wait_until(lambda: bool(ws._pending_commands))

        await server.stop()
        with pytest.raises(
            NetlinkConnectionError,
            match="Disconnected while waiting",
        ):
            await command_task
        assert not ws._pending_commands

        await _wait_until(lambda: len(connection_errors) >= 2)
        assert all(error["type"] == "transport" for error in connection_errors)

        replacement = await LocalSocketIOServer.start(port=port)
        await _wait_until(lambda: ws.connected and connections == 2)

        attempts_before_shutdown = replacement.connect_attempts
        await ws.disconnect()
        await asyncio.sleep(0.2)
        assert not ws.connected
        assert replacement.connect_attempts == attempts_before_shutdown
    finally:
        await ws.disconnect()
        if replacement is not None:
            await replacement.stop()


async def test_socketio_authentication_refusal_is_distinct_and_sanitized() -> None:
    """A real server auth refusal becomes a sanitized domain auth error."""
    server = await LocalSocketIOServer.start()
    ws = NetlinkWebSocket(
        host=f"127.0.0.1:{server.port}",
        token="rejected-secret-token",
        reconnect_delay=0.01,
        max_reconnect_delay=0.02,
    )
    connection_errors: list[dict[str, str]] = []

    @ws.on("connect_error")
    async def on_connect_error(data: dict[str, str]) -> None:
        connection_errors.append(data)

    try:
        with pytest.raises(NetlinkAuthenticationError, match="Authentication failed"):
            await ws.connect()
        await _wait_until(lambda: bool(connection_errors))

        assert connection_errors == [
            {
                "type": "authentication",
                "message": f"Authentication failed for 127.0.0.1:{server.port}",
            }
        ]
        assert "rejected-secret-token" not in str(connection_errors)
        assert server.connect_attempts == 1
    finally:
        await ws.disconnect()
        await server.stop()
