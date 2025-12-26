"""Example that listens to desk state updates only."""

import asyncio

from pynetlink import NetlinkClient

HOST = "192.0.2.10"
TOKEN = "your-bearer-token-here"  # noqa: S105


async def main() -> None:
    """Listen to desk state updates."""
    client = NetlinkClient(host=HOST, token=TOKEN)

    async with client:
        print("Connecting to Netlink device...")
        await client.connect()
        print("Connected successfully!\n")

        prev_state = {"height": None, "mode": None, "moving": None, "target": None}

        @client.on("desk.state")
        async def on_desk_state(data: dict) -> None:
            state = data.get("state", data)
            height = state.get("height")
            mode = state.get("mode")
            moving = state.get("moving", False)
            target = state.get("target")

            if (
                height != prev_state["height"]
                or mode != prev_state["mode"]
                or moving != prev_state["moving"]
                or target != prev_state["target"]
            ):
                msg = f"Height: {height}cm | Mode: {mode}"
                if target is not None:
                    msg += f" | Target: {target}cm"
                print(msg)

                prev_state["height"] = height
                prev_state["mode"] = mode
                prev_state["moving"] = moving
                prev_state["target"] = target

        print("Waiting for desk state updates...")
        await asyncio.sleep(2)

        if client.desk_state:
            print("\nCurrent desk state:")
            print(f"  Height: {client.desk_state.height}cm")
            print(f"  Mode: {client.desk_state.mode}")
            print(f"  Moving: {client.desk_state.moving}")
            if client.desk_state.target is not None:
                print(f"  Target: {client.desk_state.target}cm")
        else:
            print("\nNo desk state received yet")

        print("\n--- Listening for desk state changes (press Ctrl+C to stop) ---\n")

        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            print("\n\nStopping...")

    print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
