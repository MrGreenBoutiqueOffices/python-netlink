"""Example that listens to display state updates per bus."""

from __future__ import annotations

import asyncio

from pynetlink import NetlinkClient
from pynetlink.models import Display

HOST = "192.0.2.10"
TOKEN = "your-bearer-token-here"  # noqa: S105


def format_display_state(display: Display) -> str:
    """Build a readable string for the display state.

    Note: Display now has nested structure:
    - Top-level: bus, model, type, supports, serial_number, source_options
    - Nested state: state.power, state.source, state.brightness,
      state.volume, state.error
    """
    state_values = display.state
    result = f"Bus {display.bus} ({display.model})"
    if display.serial_number:
        result += f" [SN: {display.serial_number}]"
    result += (
        f": power={state_values.power} source={state_values.source} "
        f"brightness={state_values.brightness} volume={state_values.volume}"
    )
    if state_values.error:
        result += f" ERROR={state_values.error}"
    return result


async def main() -> None:
    """Listen for display state changes and print deltas."""
    async with NetlinkClient(host=HOST, token=TOKEN) as client:
        await client.connect()
        print("Connected to Netlink WebSocket\n")

        # Store previous states using parsed Display objects
        previous: dict[str, str] = {}

        @client.on("display.state")
        async def on_display_state(raw_event: dict) -> None:
            """Display state event callback.

            The raw event contains the updated display data.
            We parse it to Display and compare with previous state.
            """
            # Extract the display data from the event envelope
            event_data = raw_event.get("data", raw_event)

            # Parse to Display to get proper structure
            display = Display.from_dict(event_data)
            bus_id = str(display.bus)

            # Create a simple state fingerprint for comparison
            state_str = (
                f"{display.state.power}-{display.state.source}-"
                f"{display.state.brightness}-{display.state.volume}"
            )

            # Only print if state actually changed
            if previous.get(bus_id) != state_str:
                print(format_display_state(display))
                previous[bus_id] = state_str

        print("Listening for display.state updates (Ctrl+C to stop)...")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            print("\nStopping display listener...")


if __name__ == "__main__":
    asyncio.run(main())
