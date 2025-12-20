"""Device discovery example using mDNS."""

from __future__ import annotations

import asyncio

from pynetlink import NetlinkClient


async def main() -> None:
    """Discover Netlink devices on local network."""
    print("Discovering Netlink devices via mDNS...")
    print("This will take 5 seconds...\n")

    devices = await NetlinkClient.discover_devices(discovery_timeout=5.0)

    if not devices:
        print("No devices found!")
        return

    print(f"Found {len(devices)} device(s):\n")

    for device in devices:
        print(f"Device: {device.device_name}")
        print(f"  Host: {device.host}:{device.port}")
        print(f"  Device ID: {device.device_id}")
        print(f"  Model: {device.model}")
        print(f"  Version: {device.version}")
        print(f"  API Version: {device.api_version}")
        print(f"  Has desk: {device.has_desk}")
        print(
            f"  Monitors: {', '.join(device.monitors) if device.monitors else 'None'}"
        )
        print(f"  WebSocket path: {device.ws_path}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
