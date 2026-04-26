"""Example showing configured login methods and daily access codes.

Before running, copy examples/.env.example to examples/.env and fill in your values.
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from pynetlink import AuthMethod, NetlinkNotFoundError
from pynetlink.rest import NetlinkREST

load_dotenv()

if not (host := os.getenv("NETLINK_HOST")) or not (token := os.getenv("NETLINK_TOKEN")):
    MSG = "Please set NETLINK_HOST and NETLINK_TOKEN in examples/.env"
    raise ValueError(MSG)

HOST: str = host
TOKEN: str = token


def _method_summary(method: AuthMethod) -> str:
    """Return a human-readable login method summary."""
    methods = []
    if method.password:
        methods.append("password")
    if method.pin:
        methods.append(f"{method.pin_type or 'unknown'} PIN")
    return ", ".join(methods) if methods else "disabled"


async def main() -> None:
    """Read configured login methods and current daily access codes."""
    rest = NetlinkREST(host=HOST, token=TOKEN)

    try:
        auth_methods = await rest.get_auth_methods()
        for key, label in (
            ("web_login", "Web login"),
            ("signing_maintenance", "Signing maintenance"),
        ):
            method = getattr(auth_methods, key)
            if method is None:
                print(f"{label}: not configured")
                continue

            print(f"{label}: {_method_summary(method)}")
            if method.pin_length is not None:
                print(f"  PIN length: {method.pin_length}")

        try:
            access_codes = await rest.get_access_codes()
        except NetlinkNotFoundError:
            print("Daily access codes are not available on this device.")
            return

        for key, label in (
            ("web_login", "Web login"),
            ("signing_maintenance", "Signing maintenance"),
        ):
            access_code = getattr(access_codes, key)
            if access_code is None:
                print(f"{label}: no current daily access code")
                continue

            print(
                f"{label}: {access_code.code} "
                f"(valid until {access_code.valid_until}, {access_code.timezone})"
            )
    finally:
        await rest.close()


if __name__ == "__main__":
    asyncio.run(main())
