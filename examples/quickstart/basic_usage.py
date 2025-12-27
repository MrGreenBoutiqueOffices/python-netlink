"""Basic usage example for pynetlink.

Before running, copy examples/.env.example to examples/.env and fill in your values.
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from pynetlink import NetlinkClient

load_dotenv()

if not (host := os.getenv("NETLINK_HOST")) or not (token := os.getenv("NETLINK_TOKEN")):
    MSG = "Please set NETLINK_HOST and NETLINK_TOKEN in examples/.env"
    raise ValueError(MSG)

HOST: str = host
TOKEN: str = token


async def main() -> None:
    """Demonstrate basic pynetlink usage."""
    client = NetlinkClient(host=HOST, token=TOKEN)

    async with client:
        print("Connecting to Netlink device...")
        await client.connect()
        print(f"Connected: {client.connected}")

        @client.on("desk.state")
        async def on_desk_state(data: dict) -> None:
            state = data.get("state", data)
            print(
                f"Desk state update: height={state['height']}cm, mode={state['mode']}"
            )

        @client.on("display.state")
        async def on_display_state(_data: dict) -> None:
            # Use client.displays for parsed Display objects
            for bus_id, display in client.displays.items():
                print(
                    f"Display {bus_id} ({display.model}): "
                    f"power={display.state.power}, "
                    f"brightness={display.state.brightness}"
                )

        @client.on("device.info")
        async def on_device_info(data: dict) -> None:
            print(
                f"Device info: {data.get('device_name')} "
                f"({data.get('model')}) v{data.get('version')}"
            )

        await asyncio.sleep(2)

        if client.desk_state:
            print(f"\nCurrent desk height: {client.desk_state.height}cm")
            print(f"Desk mode: {client.desk_state.mode}")
            print(f"Desk moving: {client.desk_state.moving}")

        if client.device_info:
            print(f"\nDevice name: {client.device_info.device_name}")
            print(f"Device model: {client.device_info.model}")
            print(f"Device version: {client.device_info.version}")

        print("\nFetching desk status via REST API...")
        desk = await client.get_desk_status()
        print(f"Desk height: {desk.state.height} cm")

        print("\nFetching device info via REST API...")
        device_info = await client.get_device_info()
        print(f"Device ID: {device_info.device_id}")

        print("\nSetting desk height to 110 cm...")
        response = await client.set_desk_height(110.0)
        print(f"Response: {response}")

        print("\nFetching displays...")
        displays = await client.get_displays()
        for display in displays:
            print(f"  - Display {display.id}: {display.model} on bus {display.bus}")

        if displays:
            bus_id = displays[0].bus
            print(f"\nControlling display on bus {bus_id}...")

            await client.set_display_brightness(bus_id, 80)
            print("Brightness set to 80")

            await client.set_display_power(bus_id, "on")
            print("Power set to ON")

        print("\nListening for events (10 seconds)...")
        await asyncio.sleep(10)

        print("\nDisconnecting...")


if __name__ == "__main__":
    asyncio.run(main())
