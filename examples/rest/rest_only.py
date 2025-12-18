"""Example showing how to use the REST client without WebSocket."""

from __future__ import annotations

import asyncio

from pynetlink.rest import NetlinkREST

HOST = "192.0.2.10"
TOKEN = "your-bearer-token-here"  # noqa: S105
TARGET_HEIGHT = 105


async def main() -> None:
    """Interact with the desk and monitors using only REST endpoints."""
    rest = NetlinkREST(host=HOST, token=TOKEN)

    try:
        desk_status = await rest.get_desk_status()
        print(
            "Desk status:",
            f"height={desk_status.height}cm",
            f"mode={desk_status.mode}",
            f"moving={desk_status.moving}",
            f"controller={desk_status.controller_connected}",
        )

        print(f"Setting desk height to {TARGET_HEIGHT}cm")
        await rest.set_desk_height(TARGET_HEIGHT)

        monitors = await rest.get_monitors()
        if not monitors:
            print("No monitors detected")
        else:
            first = monitors[0]
            print(f"First monitor: bus={first.bus} model={first.model}")
            await rest.set_monitor_brightness(first.bus, 75)
            await rest.set_monitor_power(first.bus, "on")
            info = await rest.get_monitor_status(first.bus)
            print(
                "Monitor status:",
                f"power={info.power}",
                f"brightness={info.brightness}",
                f"source={info.source}",
            )
    finally:
        await rest.close()


if __name__ == "__main__":
    asyncio.run(main())
