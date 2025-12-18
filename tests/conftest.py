"""Fixtures for the pynetlink tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from aiohttp import ClientSession

from pynetlink import NetlinkClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest.fixture(name="netlink_client")
async def client() -> AsyncGenerator[NetlinkClient, None]:
    """Return a NetlinkClient instance.

    This creates a client without connecting to avoid real network calls.
    Individual tests can call await client.connect() if needed.
    """
    async with (
        ClientSession() as session,
        NetlinkClient(
            host="192.168.1.100", token="test-token", session=session
        ) as netlink_client,
    ):
        yield netlink_client
