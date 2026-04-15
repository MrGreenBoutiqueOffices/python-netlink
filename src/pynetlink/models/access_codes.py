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

    web_login: AccessCode
    signing_maintenance: AccessCode
