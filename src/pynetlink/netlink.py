"""Main Netlink client facade."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

from .const import (
    DEFAULT_REQUEST_TIMEOUT,
    EVENT_DESK_STATE,
    EVENT_DEVICE_INFO,
    EVENT_DISPLAY_STATE,
)
from .models import (
    Desk,
    DeskState,
    DeviceInfo,
    Display,
    DisplaySummary,
    NetlinkDevice,
)
from .rest import NetlinkREST
from .websocket import NetlinkWebSocket

if TYPE_CHECKING:
    from collections.abc import Callable

    import aiohttp  # pyright: ignore[reportMissingImports]


@dataclass
class NetlinkClient:
    """Asynchronous client for Netlink devices.

    Combines WebSocket (real-time events) and REST API (commands).

    Args:
    ----
        host: Hostname or IP address
        token: Bearer authentication token
        request_timeout: REST request timeout (default: 5s)
        session: Optional aiohttp ClientSession

    Examples:
    --------
        >>> async with NetlinkClient("192.168.1.100", "token") as client:
        >>>     await client.connect()
        >>>     print(client.desk_state.height)

    """

    host: str
    token: str
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT
    session: aiohttp.ClientSession | None = None

    # Internal components
    _ws: NetlinkWebSocket = field(init=False, repr=False)
    _rest: NetlinkREST = field(init=False, repr=False)
    _close_session: bool = field(default=False, init=False, repr=False)

    # State cache from WebSocket
    _desk_state: DeskState | None = field(default=None, init=False, repr=False)
    _displays: dict[str, Display] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _device_info: DeviceInfo | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize WebSocket and REST clients."""
        self._ws = NetlinkWebSocket(self.host, self.token)
        self._rest = NetlinkREST(self.host, self.token, self.request_timeout)

        # Wire up WebSocket events to update internal state
        self._ws.on(EVENT_DESK_STATE)(self._on_desk_state)
        self._ws.on(EVENT_DISPLAY_STATE)(self._on_display_state)
        self._ws.on(EVENT_DEVICE_INFO)(self._on_device_info)

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect WebSocket to receive real-time events.

        Raises
        ------
            NetlinkAuthenticationError: Invalid token
            NetlinkConnectionError: Connection failed
            NetlinkTimeoutError: Connection timeout

        """
        await self._ws.connect()

    async def disconnect(self) -> None:
        """Disconnect WebSocket and close session."""
        await self._ws.disconnect()
        await self._rest.close()
        if self.session and self._close_session:
            await self.session.close()

    def on(self, event: str) -> Callable[[Callable], Callable]:
        """Subscribe to WebSocket events.

        Args:
        ----
            event: Event name (e.g., "desk.state")

        Returns:
        -------
            Decorator function

        Examples:
        --------
            >>> @client.on("desk.state")
            >>> async def handle_desk(state: DeskState):
            >>>     print(f"Height: {state.height}")

        """
        return self._ws.on(event)

    # Internal event handlers
    async def _on_desk_state(self, data: str | dict[str, Any]) -> None:
        """Update internal desk state from WebSocket."""
        # Ensure payload is parsed (fixtures may supply JSON strings)
        payload = json.loads(data) if isinstance(data, str) else data
        # Extract actual state data from envelope
        envelope_data = payload.get("data", payload)
        # Extract nested state from {capabilities, inventory, state: {...}}
        # Fallback to flat structure for backward compatibility
        state_data = envelope_data.get("state", envelope_data)
        self._desk_state = DeskState.from_dict(state_data)

    async def _on_display_state(self, data: str | dict[str, Any]) -> None:
        """Update internal display state from WebSocket."""
        # Ensure payload is parsed (fixtures may supply JSON strings)
        payload = json.loads(data) if isinstance(data, str) else data
        # Extract actual state data from nested structure
        state_data = payload.get("data", payload)
        display = Display.from_dict(state_data)
        # Use string bus_id as key
        bus_key = str(display.bus)
        self._displays[bus_key] = display

    async def _on_device_info(self, data: str | dict[str, Any]) -> None:
        """Update internal device info from WebSocket."""
        # Ensure payload is parsed (fixtures may supply JSON strings)
        payload = json.loads(data) if isinstance(data, str) else data
        # Extract actual device info data from nested structure
        info_data = payload.get("data", payload)
        self._device_info = DeviceInfo.from_dict(info_data)

    # Properties for WebSocket state
    @property
    def desk_state(self) -> DeskState | None:
        """Latest desk state from WebSocket.

        Returns
        -------
            Current desk state or None if not connected

        """
        return self._desk_state

    @property
    def displays(self) -> dict[str, Display]:
        """Latest display states from WebSocket.

        Returns
        -------
            Dictionary mapping bus_id to Display

        """
        return self._displays

    @property
    def device_info(self) -> DeviceInfo | None:
        """Latest device info from WebSocket.

        Returns
        -------
            Current device info or None if not connected

        """
        return self._device_info

    @property
    def connected(self) -> bool:
        """Whether WebSocket is connected."""
        return self._ws.connected

    # Device information methods (delegate to REST)
    async def get_device_info(self) -> DeviceInfo:
        """Get device information.

        Returns
        -------
            Complete device information including ID, name, version, and model

        """
        return await self._rest.get_device_info()

    # Desk control methods (delegate to REST)
    async def get_desk_status(self) -> Desk:
        """Get full desk status from REST API.

        Returns
        -------
            Complete desk status including controller connection

        """
        return await self._rest.get_desk_status()

    async def set_desk_height(
        self,
        height: float,
        transport: str = "auto",
    ) -> dict[str, Any]:
        """Set target desk height.

        Args:
        ----
            height: Target height in cm (62-127)
            transport: Transport method - "auto" (WebSocket if connected, else REST),
                      "websocket" (WebSocket only), or "rest" (REST only)

        Returns:
        -------
            Confirmation response

        Raises:
        ------
            ValueError: Height out of valid range
            NetlinkConnectionError: WebSocket not connected (if transport="websocket")

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command(
                    "command.desk.height",
                    {"height": height},
                )
            return await self._rest.set_desk_height(height)
        if transport == "websocket":
            return await self._ws.send_command(
                "command.desk.height", {"height": height}
            )
        return await self._rest.set_desk_height(height)

    async def stop_desk(self, transport: str = "auto") -> dict[str, Any]:
        """Stop desk movement.

        Args:
        ----
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command("command.desk.stop")
            return await self._rest.stop_desk()
        if transport == "websocket":
            return await self._ws.send_command("command.desk.stop")
        return await self._rest.stop_desk()

    async def reset_desk(self, transport: str = "auto") -> dict[str, Any]:
        """Reset desk to factory defaults.

        Args:
        ----
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command("command.desk.reset")
            return await self._rest.reset_desk()
        if transport == "websocket":
            return await self._ws.send_command("command.desk.reset")
        return await self._rest.reset_desk()

    async def calibrate_desk(self, transport: str = "auto") -> dict[str, Any]:
        """Start desk calibration process.

        Args:
        ----
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command("command.desk.calibrate")
            return await self._rest.calibrate_desk()
        if transport == "websocket":
            return await self._ws.send_command("command.desk.calibrate")
        return await self._rest.calibrate_desk()

    async def set_desk_beep(
        self,
        *,
        state: str | bool,
        transport: str = "auto",
    ) -> dict[str, Any]:
        """Enable or disable desk beep.

        Args:
        ----
            state: "on" or "off" (bools are also accepted)
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command(
                    "command.desk.beep",
                    {"state": state},
                )
            return await self._rest.set_desk_beep(state=state)
        if transport == "websocket":
            return await self._ws.send_command("command.desk.beep", {"state": state})
        return await self._rest.set_desk_beep(state=state)

    # Display control methods (delegate to REST)
    async def get_displays(self) -> list[DisplaySummary]:
        """Get list of connected displays.

        Returns
        -------
            List of display summaries

        """
        return await self._rest.get_displays()

    async def get_display_status(self, bus_id: int | str) -> Display:
        """Get detailed display status.

        Args:
        ----
            bus_id: Display bus ID

        Returns:
        -------
            Complete display status

        """
        return await self._rest.get_display_status(bus_id)

    async def set_display_power(
        self,
        bus_id: int | str,
        state: str,
        transport: str = "auto",
    ) -> dict[str, Any]:
        """Set display power state.

        Args:
        ----
            bus_id: Display bus ID
            state: Power state ("on" or "off")
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command(
                    "command.display.power",
                    {"bus": str(bus_id), "attr": "power", "value": state},
                )
            return await self._rest.set_display_power(bus_id, state)
        if transport == "websocket":
            return await self._ws.send_command(
                "command.display.power",
                {"bus": str(bus_id), "attr": "power", "value": state},
            )
        return await self._rest.set_display_power(bus_id, state)

    async def set_display_brightness(
        self,
        bus_id: int | str,
        brightness: int,
        transport: str = "auto",
    ) -> dict[str, Any]:
        """Set display brightness level.

        Args:
        ----
            bus_id: Display bus ID
            brightness: Brightness level (0-100)
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command(
                    "command.display.brightness",
                    {"bus": str(bus_id), "attr": "brightness", "value": brightness},
                )
            return await self._rest.set_display_brightness(bus_id, brightness)
        if transport == "websocket":
            return await self._ws.send_command(
                "command.display.brightness",
                {"bus": str(bus_id), "attr": "brightness", "value": brightness},
            )
        return await self._rest.set_display_brightness(bus_id, brightness)

    async def set_display_volume(
        self,
        bus_id: int | str,
        volume: int,
        transport: str = "auto",
    ) -> dict[str, Any]:
        """Set display volume level.

        Args:
        ----
            bus_id: Display bus ID
            volume: Volume level (0-100)
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command(
                    "command.display.volume",
                    {"bus": str(bus_id), "attr": "volume", "value": volume},
                )
            return await self._rest.set_display_volume(bus_id, volume)
        if transport == "websocket":
            return await self._ws.send_command(
                "command.display.volume",
                {"bus": str(bus_id), "attr": "volume", "value": volume},
            )
        return await self._rest.set_display_volume(bus_id, volume)

    async def set_display_source(
        self,
        bus_id: int | str,
        source: str,
        transport: str = "auto",
    ) -> dict[str, Any]:
        """Set display input source.

        Args:
        ----
            bus_id: Display bus ID
            source: Input source (e.g., "HDMI1", "USBC")
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command(
                    "command.display.source",
                    {"bus": str(bus_id), "attr": "source", "value": source},
                )
            return await self._rest.set_display_source(bus_id, source)
        if transport == "websocket":
            return await self._ws.send_command(
                "command.display.source",
                {"bus": str(bus_id), "attr": "source", "value": source},
            )
        return await self._rest.set_display_source(bus_id, source)

    # Browser control methods (delegate to REST)
    async def get_browser_url(self) -> str:
        """Get current browser URL.

        Returns
        -------
            Current URL

        """
        return await self._rest.get_browser_url()

    async def set_browser_url(
        self,
        url: str,
        transport: str = "auto",
    ) -> dict[str, Any]:
        """Set browser URL.

        Args:
        ----
            url: Target URL
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command("command.browser.url", {"url": url})
            return await self._rest.set_browser_url(url)
        if transport == "websocket":
            return await self._ws.send_command("command.browser.url", {"url": url})
        return await self._rest.set_browser_url(url)

    async def refresh_browser(self, transport: str = "auto") -> dict[str, Any]:
        """Refresh browser page.

        Args:
        ----
            transport: Transport method - "auto", "websocket", or "rest"

        Returns:
        -------
            Confirmation response

        """
        if transport == "auto":
            if self._ws.connected:
                return await self._ws.send_command("command.browser.refresh")
            return await self._rest.refresh_browser()
        if transport == "websocket":
            return await self._ws.send_command("command.browser.refresh")
        return await self._rest.refresh_browser()

    # Discovery methods
    @staticmethod
    async def discover_devices(discovery_timeout: float = 5.0) -> list[NetlinkDevice]:
        """Discover Netlink devices on local network via mDNS.

        Args:
        ----
            discovery_timeout: Discovery timeout in seconds

        Returns:
        -------
            List of discovered devices

        Examples:
        --------
            >>> devices = await NetlinkClient.discover_devices()
            >>> for device in devices:
            >>>     print(f"Found: {device.name} at {device.host}")

        """
        devices: list[NetlinkDevice] = []

        class NetlinkListener(ServiceListener):
            """Capture discovered Netlink devices."""

            def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                info = zc.get_service_info(type_, name)
                if info:
                    device = NetlinkDevice.from_service_info(info)
                    devices.append(device)

            def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                pass

            def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
                pass

        zeroconf = Zeroconf()
        # Keep reference to browser (required for discovery to work)
        _browser = ServiceBrowser(zeroconf, "_netlink._tcp.local.", NetlinkListener())

        await asyncio.sleep(discovery_timeout)
        zeroconf.close()

        return devices
