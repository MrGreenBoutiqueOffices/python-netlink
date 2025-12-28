"""Exceptions for pynetlink."""

from __future__ import annotations


class NetlinkError(Exception):
    """Base exception for pynetlink."""


class NetlinkConnectionError(NetlinkError):
    """WebSocket or REST connection failed."""


class NetlinkAuthenticationError(NetlinkError):
    """Invalid bearer token."""


class NetlinkTimeoutError(NetlinkError):
    """Request timeout."""


class NetlinkCommandError(NetlinkError):
    """Command execution failed."""

    def __init__(
        self,
        message: str,
        command: str,
        error_details: dict[str, str] | None = None,
    ) -> None:
        """Initialize command error.

        Args:
        ----
            message: Error message
            command: Command that failed
            error_details: Additional error details

        """
        super().__init__(message)
        self.command = command
        self.error_details = error_details


class NetlinkDataError(NetlinkError):
    """Invalid or incomplete data received from device."""
