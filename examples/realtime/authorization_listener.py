"""Inspect effective Socket.IO authorization without polling."""

import asyncio
import os

from dotenv import load_dotenv

from pynetlink import (
    EVENT_AUTHORIZATION_STATE,
    NetlinkClient,
    NetlinkMaintenanceRequiredError,
)

load_dotenv()

if not (host := os.getenv("NETLINK_HOST")) or not (token := os.getenv("NETLINK_TOKEN")):
    MSG = "Please set NETLINK_HOST and NETLINK_TOKEN in examples/.env"
    raise ValueError(MSG)

HOST: str = host
TOKEN: str = token


async def main() -> None:
    """Print authorization changes and handle a typed denial."""
    async with NetlinkClient(host=HOST, token=TOKEN) as client:

        @client.on(EVENT_AUTHORIZATION_STATE)
        async def on_authorization_state(_data: dict) -> None:
            state = client.authorization_state
            if state is None:
                return
            print(f"Allowed commands: {sorted(state.allowed_commands)}")
            print(f"Maintenance granted: {state.maintenance.granted}")
            print(f"Maintenance valid until: {state.maintenance.valid_until}")

        await client.connect()
        await asyncio.sleep(1)

        state = client.authorization_state
        if state is None:
            print("Authorization discovery is not available on this server.")
        elif state.allows_command("command.system.reboot"):
            print("System reboot is currently allowed.")

        try:
            await client.reboot_device()
        except NetlinkMaintenanceRequiredError:
            print("System reboot requires an active maintenance grant.")


if __name__ == "__main__":
    asyncio.run(main())
