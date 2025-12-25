"""Discovery data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zeroconf import ServiceInfo


@dataclass
class NetlinkDevice:
    """Discovered Netlink device via mDNS.

    Attributes
    ----------
        host: IP address or hostname
        port: WebSocket/HTTP port
        device_id: Unique device identifier
        device_name: Device name
        model: Device model
        version: Software version
        api_version: API version
        has_desk: Whether device has desk control
        displays: List of connected display bus IDs
        ws_path: WebSocket path

    """

    host: str
    port: int
    device_id: str
    device_name: str
    model: str
    version: str
    api_version: str
    has_desk: bool
    displays: list[str]
    ws_path: str

    @classmethod
    def from_service_info(cls, info: ServiceInfo) -> NetlinkDevice:
        """Create NetlinkDevice from Zeroconf ServiceInfo.

        Args:
        ----
            info: Zeroconf service information

        Returns:
        -------
            NetlinkDevice instance

        """
        properties: dict[str, str] = {}
        if info.properties:
            properties = {
                (k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else str(k)): (
                    v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else str(v)
                )
                for k, v in info.properties.items()
                if k is not None and v is not None
            }

        host = info.parsed_addresses()[0] if info.parsed_addresses() else ""
        port = int(info.port) if info.port is not None else 0

        return cls(
            host=host,
            port=port,
            device_id=properties.get("device_id", ""),
            device_name=properties.get("device_name", "Unknown"),
            model=properties.get("model", ""),
            version=properties.get("version", ""),
            api_version=properties.get("api_version", "v1"),
            has_desk=properties.get("has_desk", "false") == "true",
            displays=(
                properties.get("displays", "").split(",")
                if properties.get("displays")
                else []
            ),
            ws_path=properties.get("ws_path", "/socket.io"),
        )
