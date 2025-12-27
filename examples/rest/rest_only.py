"""Example showing how to use the REST client without WebSocket.

Before running, copy examples/.env.example to examples/.env and fill in your values.
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from pynetlink.rest import NetlinkREST

load_dotenv()

if not (host := os.getenv("NETLINK_HOST")) or not (token := os.getenv("NETLINK_TOKEN")):
    MSG = "Please set NETLINK_HOST and NETLINK_TOKEN in examples/.env"
    raise ValueError(MSG)

HOST: str = host
TOKEN: str = token
TARGET_HEIGHT = 105


async def main() -> None:
    """Interact with the desk and displays using only REST endpoints."""
    rest = NetlinkREST(host=HOST, token=TOKEN)

    try:
        desk = await rest.get_desk_status()
        print(
            "Desk status:",
            f"height={desk.state.height}cm",
            f"mode={desk.state.mode}",
            f"moving={desk.state.moving}",
            f"beep={desk.state.beep}",
        )

        print(f"Setting desk height to {TARGET_HEIGHT}cm")
        await rest.set_desk_height(TARGET_HEIGHT)

        displays = await rest.get_displays()
        if not displays:
            print("No displays detected")
        else:
            first = displays[0]
            print(f"First display: bus={first.bus} model={first.model}")
            await rest.set_display_brightness(first.bus, 75)
            await rest.set_display_power(first.bus, "on")
            info = await rest.get_display_status(first.bus)
            print(
                "Display status:",
                f"power={info.state.power}",
                f"brightness={info.state.brightness}",
                f"source={info.state.source}",
            )
    finally:
        await rest.close()


if __name__ == "__main__":
    asyncio.run(main())
