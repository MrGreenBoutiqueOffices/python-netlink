"""Browser data models."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro import DataClassDictMixin


@dataclass
class BrowserState(DataClassDictMixin):
    """Browser state from REST API `/api/v1/browser/status`.

    Attributes
    ----------
        url: Current browser URL
        default_url: Default browser URL

    """

    url: str
    default_url: str | None = None
