"""Example that listens to monitor state updates per bus."""

from __future__ import annotations

import asyncio
from typing import Any

from pynetlink import NetlinkClient

HOST = "192.0.2.10"
TOKEN = "your-bearer-token-here"  # noqa: S105


def format_monitor_state(state: dict[str, Any]) -> str:
    """Build a readable string for the incoming monitor state."""
    bus = state.get("bus")
    power = state.get("power")
    brightness = state.get("brightness")
    volume = state.get("volume")
    source = state.get("source")
    return (
        f"Bus {bus}: power={power} brightness={brightness} volume={volume}"
        f" source={source}"
    )


async def main() -> None:
    """Listen for monitor state changes and print deltas."""
    async with NetlinkClient(host=HOST, token=TOKEN) as client:
        await client.connect()
        print("Connected to Netlink WebSocket\n")

        previous: dict[str, dict[str, Any]] = {}

        @client.on("monitor.state")
        async def on_monitor_state(state: dict[str, Any]) -> None:
            bus = str(state.get("bus"))
            old = previous.get(bus)
            if old != state:
                print(format_monitor_state(state))
                previous[bus] = state

        print("Listening for monitor.state updates (Ctrl+C to stop)...")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            print("\nStopping monitor listener...")


if __name__ == "__main__":
    asyncio.run(main())
