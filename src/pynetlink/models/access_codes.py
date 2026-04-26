"""Access code data models."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass
class AccessCode(DataClassDictMixin):
    """Access code entry from REST API `/api/v1/admin/access-codes`."""

    code: str
    valid_from: str
    valid_until: str
    timezone: str


@dataclass
class AccessCodes(DataClassDictMixin):
    """Current access codes for privileged admin clients."""

    web_login: AccessCode | None = None
    signing_maintenance: AccessCode | None = None


@dataclass
class AuthMethod(DataClassDictMixin):
    """Authentication method metadata for one access purpose."""

    password: bool = False
    pin: bool = False
    pin_length: int | None = None
    pin_type: str | None = None


@dataclass
class AuthMethods(DataClassDictMixin):
    """Available authentication methods per access purpose."""

    web_login: AuthMethod | None = None
    signing_maintenance: AuthMethod | None = None
