"""Example demonstrating browser control endpoints.

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
