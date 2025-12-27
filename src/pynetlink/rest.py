"""REST API client for Netlink devices."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Self

from aiohttp import ClientError, ClientResponseError, ClientSession, TCPConnector
from aiohttp.hdrs import METH_GET, METH_PATCH, METH_POST, METH_PUT
from yarl import URL

from .const import API_VERSION, DEFAULT_REQUEST_TIMEOUT
from .exceptions import (
    NetlinkAuthenticationError,
    NetlinkConnectionError,
    NetlinkTimeoutError,
)
from .models import BrowserState, Desk, DeviceInfo, Display, DisplaySummary

VERSION = metadata.version(__package__ or "pynetlink")


@dataclass
class NetlinkREST:
    """REST API client for Netlink commands.

    Args:
    ----
        host: Hostname or IP address
        token: Bearer authentication token
        request_timeout: Request timeout in seconds

    """

    host: str
    token: str
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT

    # Internal state
    _session: ClientSession | None = None
    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        method: str = METH_GET,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make REST API request.

        Args:
        ----
            uri: API endpoint (e.g., "desk/height")
            method: HTTP method (GET, POST, PUT, PATCH)

        Returns:
        -------
            Parsed JSON response

        Raises:
        ------
            NetlinkAuthenticationError: Invalid token (401)
            NetlinkConnectionError: Network error
            NetlinkTimeoutError: Request timeout

        """
        url = URL.build(
            scheme="http",
            host=self.host,
            path=f"/api/{API_VERSION}/",
        ).join(URL(uri))

        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": f"pynetlink/{VERSION}",
        }

        if self._session is None:
            self._session = ClientSession(connector=TCPConnector(force_close=True))
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self._session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json,
                )
                response.raise_for_status()

        except TimeoutError as err:
            msg = f"Request to {url} timed out"
            raise NetlinkTimeoutError(msg) from err
        except ClientResponseError as err:
            if err.status == 401:
                msg = f"Authentication failed for {self.host}"
                raise NetlinkAuthenticationError(msg) from err
            if err.status == 405:
                msg = f"HTTP method {method} not allowed for {url}"
                raise NetlinkConnectionError(msg) from err
            msg = f"HTTP error {err.status} for {url}: {err.message}"
            raise NetlinkConnectionError(msg) from err
        except ClientError as err:
            msg = f"Request to {url} failed: {err}"
            raise NetlinkConnectionError(msg) from err

        return await response.json()

    # Device endpoints
    async def get_device_info(self) -> DeviceInfo:
        """Get device information.

        Returns
        -------
            Complete device information including ID, name, version, and model

        """
        data = await self._request("device/info")
        return DeviceInfo.from_dict(data)

    # Desk endpoints
    async def get_desk_status(self) -> Desk:
        """Get full desk status.

        Returns
        -------
            Complete desk status

        """
        data = await self._request("desk/status")
        return Desk.from_dict(data)

    async def set_desk_height(self, height: float) -> dict[str, Any]:
        """Set target desk height.

        Args:
        ----
            height: Target height in cm (62-127)

        Returns:
        -------
            Confirmation response with height and status

        Raises:
        ------
            ValueError: Height out of valid range

        """
        if not 62.0 <= height <= 127.0:
            msg = f"Height must be between 62 and 127 cm, got {height}"
            raise ValueError(msg)

        return await self._request(
            "desk/height", method=METH_POST, json={"height": height}
        )

    async def stop_desk(self) -> dict[str, Any]:
        """Stop desk movement.

        Returns
        -------
            Confirmation response

        """
        return await self._request("desk/stop", method=METH_POST)

    async def reset_desk(self) -> dict[str, Any]:
        """Reset desk to factory defaults.

        Returns
        -------
            Confirmation response

        """
        return await self._request("desk/reset", method=METH_POST)

    async def calibrate_desk(self) -> dict[str, Any]:
        """Start desk calibration process.

        Returns
        -------
            Confirmation response

        """
        return await self._request("desk/calibrate", method=METH_POST)

    async def set_desk_beep(self, *, state: str | bool) -> dict[str, Any]:
        """Enable or disable desk beep.

        Args:
        ----
            state: "on" or "off" (bools are also accepted)

        Returns:
        -------
            Confirmation response

        Raises:
        ------
            ValueError: Invalid state

        """
        if isinstance(state, bool):
            state = "on" if state else "off"
        if state not in {"on", "off"}:
            msg = f"Beep state must be 'on' or 'off', got {state}"
            raise ValueError(msg)

        return await self._request("desk/beep", method=METH_POST, json={"state": state})

    # Display endpoints
    async def get_displays(self) -> list[DisplaySummary]:
        """Get list of connected displays.

        Returns
        -------
            List of display summaries

        """
        data = await self._request("displays")
        # API returns list directly
        if isinstance(data, list):
            return [DisplaySummary.from_dict(m) for m in data]
        # Or wrapped in dict with "displays" key
        return [DisplaySummary.from_dict(m) for m in data.get("displays", [])]

    async def get_display_status(self, bus_id: int | str) -> Display:
        """Get detailed display status.

        Args:
        ----
            bus_id: Display bus ID

        Returns:
        -------
            Complete display status

        """
        data = await self._request(f"display/{bus_id}/status")
        return Display.from_dict(data)

    async def get_display_power(self, bus_id: int | str) -> str | None:
        """Get display power state.

        Args:
        ----
            bus_id: Display bus ID

        Returns:
        -------
            Power state ("on", "off", "standby")

        """
        data = await self._request(f"display/{bus_id}/power")
        return data.get("state")

    async def set_display_power(self, bus_id: int | str, state: str) -> dict[str, Any]:
        """Set display power state.

        Args:
        ----
            bus_id: Display bus ID
            state: Power state ("on" or "off")

        Returns:
        -------
            Confirmation response

        """
        return await self._request(
            f"display/{bus_id}/power",
            method=METH_PUT,
            json={"state": state},
        )

    async def get_display_source(self, bus_id: int | str) -> str | None:
        """Get display input source.

        Args:
        ----
            bus_id: Display bus ID

        Returns:
        -------
            Current input source

        """
        data = await self._request(f"display/{bus_id}/source")
        return data.get("source")

    async def set_display_source(
        self,
        bus_id: int | str,
        source: str,
    ) -> dict[str, Any]:
        """Set display input source.

        Args:
        ----
            bus_id: Display bus ID
            source: Input source (e.g., "HDMI1", "USBC")

        Returns:
        -------
            Confirmation response

        """
        return await self._request(
            f"display/{bus_id}/source",
            method=METH_PUT,
            json={"source": source},
        )

    async def get_display_brightness(self, bus_id: int | str) -> int | None:
        """Get display brightness level.

        Args:
        ----
            bus_id: Display bus ID

        Returns:
        -------
            Brightness level (0-100)

        """
        data = await self._request(f"display/{bus_id}/brightness")
        return data.get("brightness")

    async def set_display_brightness(
        self,
        bus_id: int | str,
        brightness: int,
    ) -> dict[str, Any]:
        """Set display brightness level.

        Args:
        ----
            bus_id: Display bus ID
            brightness: Brightness level (0-100)

        Returns:
        -------
            Confirmation response

        Raises:
        ------
            ValueError: Brightness out of range

        """
        if not 0 <= brightness <= 100:
            msg = f"Brightness must be between 0 and 100, got {brightness}"
            raise ValueError(msg)

        return await self._request(
            f"display/{bus_id}/brightness",
            method=METH_PUT,
            json={"brightness": brightness},
        )

    async def get_display_volume(self, bus_id: int | str) -> int | None:
        """Get display volume level.

        Args:
        ----
            bus_id: Display bus ID

        Returns:
        -------
            Volume level (0-100)

        """
        data = await self._request(f"display/{bus_id}/volume")
        return data.get("volume")

    async def set_display_volume(
        self,
        bus_id: int | str,
        volume: int,
    ) -> dict[str, Any]:
        """Set display volume level.

        Args:
        ----
            bus_id: Display bus ID
            volume: Volume level (0-100)

        Returns:
        -------
            Confirmation response

        Raises:
        ------
            ValueError: Volume out of range

        """
        if not 0 <= volume <= 100:
            msg = f"Volume must be between 0 and 100, got {volume}"
            raise ValueError(msg)

        return await self._request(
            f"display/{bus_id}/volume",
            method=METH_PUT,
            json={"volume": volume},
        )

    async def patch_display(
        self,
        bus_id: int | str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update multiple display properties at once.

        Args:
        ----
            bus_id: Display bus ID
            **kwargs: Properties to update (power, brightness, volume, source)

        Returns:
        -------
            Confirmation response

        """
        return await self._request(f"display/{bus_id}", method=METH_PATCH, json=kwargs)

    # Browser endpoints
    async def get_browser_url(self) -> str:
        """Get current browser URL.

        Returns
        -------
            Current URL

        """
        data = await self._request("browser/url")
        return data.get("url", "")

    async def set_browser_url(self, url: str) -> dict[str, Any]:
        """Set browser URL.

        Args:
        ----
            url: Target URL

        Returns:
        -------
            Confirmation response

        """
        return await self._request("browser/url", method=METH_POST, json={"url": url})

    async def get_browser_status(self) -> BrowserState:
        """Get browser status.

        Returns
        -------
            Browser state with URL and status

        """
        data = await self._request("browser/status")
        return BrowserState.from_dict(data)

    async def refresh_browser(self) -> dict[str, Any]:
        """Refresh browser page.

        Returns
        -------
            Confirmation response

        """
        return await self._request("browser/refresh", method=METH_POST)

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The NetlinkREST object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
