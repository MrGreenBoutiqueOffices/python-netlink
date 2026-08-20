"""Socket.IO authorization state models."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

from pynetlink.exceptions import NetlinkDataError

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class MaintenanceAuthorization:
    """Effective maintenance grant reported by the server."""

    granted: bool
    valid_until: str | None


@dataclass(frozen=True)
class AuthorizationState:
    """Effective Socket.IO policy for the current connection.

    The command set and event-audience mapping are immutable snapshots. A missing
    state means the connected server does not advertise authorization discovery.
    """

    policy_version: int
    allowed_commands: frozenset[str]
    event_audiences: Mapping[str, bool]
    maintenance: MaintenanceAuthorization

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthorizationState:
        """Create an authorization snapshot from a version 1 event payload."""
        try:
            policy_version = data["policy_version"]
            allowed_commands = data["allowed_commands"]
            event_audiences = data["event_audiences"]
            maintenance = data["maintenance"]
        except (KeyError, TypeError) as err:
            msg = "Incomplete authorization state data"
            raise NetlinkDataError(msg) from err

        if not isinstance(policy_version, int) or isinstance(policy_version, bool):
            msg = "Invalid authorization policy_version"
            raise NetlinkDataError(msg)
        if not isinstance(allowed_commands, list) or not all(
            isinstance(command, str) for command in allowed_commands
        ):
            msg = "Invalid authorization allowed_commands"
            raise NetlinkDataError(msg)
        typed_allowed_commands = cast("list[str]", allowed_commands)
        if not isinstance(event_audiences, dict) or not all(
            isinstance(event, str) and isinstance(allowed, bool)
            for event, allowed in event_audiences.items()
        ):
            msg = "Invalid authorization event_audiences"
            raise NetlinkDataError(msg)
        if not isinstance(maintenance, dict):
            msg = "Invalid authorization maintenance data"
            raise NetlinkDataError(msg)

        granted = maintenance.get("granted")
        valid_until = maintenance.get("valid_until")
        if not isinstance(granted, bool) or (
            valid_until is not None and not isinstance(valid_until, str)
        ):
            msg = "Invalid authorization maintenance data"
            raise NetlinkDataError(msg)

        return cls(
            policy_version=policy_version,
            allowed_commands=frozenset(typed_allowed_commands),
            event_audiences=MappingProxyType(dict(event_audiences)),
            maintenance=MaintenanceAuthorization(
                granted=granted,
                valid_until=valid_until,
            ),
        )

    def allows_command(self, command: str) -> bool:
        """Return whether the current policy permits a command."""
        return command in self.allowed_commands

    def receives_event(self, event: str) -> bool | None:
        """Return the advertised audience decision, if security-relevant."""
        return self.event_audiences.get(event)
