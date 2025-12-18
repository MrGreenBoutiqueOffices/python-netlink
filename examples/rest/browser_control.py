"""Example demonstrating browser control endpoints."""

from __future__ import annotations

import asyncio

from pynetlink.rest import NetlinkREST

HOST = "192.0.2.10"
TOKEN = "your-bearer-token-here"  # noqa: S105
BROWSER_URL = "https://google.com"


async def main() -> None:
    """Set, read and refresh the browser service via REST only."""
    rest = NetlinkREST(host=HOST, token=TOKEN)
    try:
        print(f"Setting browser URL to {BROWSER_URL}")
        await rest.set_browser_url(BROWSER_URL)

        status = await rest.get_browser_status()
        print("Browser status:")
        print(f"  URL: {status.url}")

        await asyncio.sleep(2)
        print("Triggering browser refresh...")
        await rest.refresh_browser()

        print("Done.")
    finally:
        await rest.close()


if __name__ == "__main__":
    asyncio.run(main())
