"""Basic usage example for pynetlink."""

from __future__ import annotations

import asyncio

from pynetlink import NetlinkClient

HOST = "192.0.2.10"
TOKEN = "your-bearer-token-here"  # noqa: S105


async def main() -> None:
    """Demonstrate basic pynetlink usage."""
    client = NetlinkClient(host=HOST, token=TOKEN)

    async with client:
        print("Connecting to Netlink device...")
        await client.connect()
        print(f"Connected: {client.connected}")

        @client.on("desk.state")
        async def on_desk_state(data: dict) -> None:
            print(f"Desk state update: height={data['height']}cm, mode={data['mode']}")

        @client.on("monitor.state")
        async def on_monitor_state(data: dict) -> None:
            print(
                f"Monitor {data['bus']}: power={data.get('power')}, "
                f"brightness={data.get('brightness')}"
            )

        await asyncio.sleep(2)

        if client.desk_state:
            print(f"\nCurrent desk height: {client.desk_state.height}cm")
            print(f"Desk mode: {client.desk_state.mode}")
            print(f"Desk moving: {client.desk_state.moving}")

        print("\nFetching desk status via REST API...")
        desk_status = await client.get_desk_status()
        print(f"Controller connected: {desk_status.controller_connected}")

        print("\nSetting desk height to 110cm...")
        response = await client.set_desk_height(110.0)
        print(f"Response: {response}")

        print("\nFetching monitors...")
        monitors = await client.get_monitors()
        for monitor in monitors:
            print(f"  - Monitor {monitor.id}: {monitor.model} on bus {monitor.bus}")

        if monitors:
            bus_id = monitors[0].bus
            print(f"\nControlling monitor on bus {bus_id}...")

            await client.set_monitor_brightness(bus_id, 80)
            print("Brightness set to 80")

            await client.set_monitor_power(bus_id, "on")
            print("Power set to ON")

        print("\nListening for events (10 seconds)...")
        await asyncio.sleep(10)

        print("\nDisconnecting...")


if __name__ == "__main__":
    asyncio.run(main())
